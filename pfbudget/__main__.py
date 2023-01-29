from decimal import Decimal
from typing import Sequence

from pfbudget.cli.runnable import argparser
from pfbudget.common.types import Operation
from pfbudget.core.manager import Manager
import pfbudget.db.model as type
from pfbudget.utils.utils import parse_args_period


def interactive(manager: Manager):
    with manager.db.session() as session:

        categories = session.get(type.Category)
        print(f"Available categories: {[c.name for c in categories]}")
        tags = session.get(type.Tag)
        print(f"Available tags: {[t.name for t in tags]}")

        transactions = session.uncategorized()
        print(f"{len(transactions)} transactions left to categorize")

        for transaction in sorted(transactions):
            print(f"{transaction}")
            quit = False
            next = True
            while next:
                match (input("(<category>/split/tag/note/skip/quit): ")):
                    case "skip":
                        next = False
                        continue

                    case "quit" | "exit":
                        next = False
                        quit = True

                    case "split":
                        manager.action(Operation.Split, split(transaction, categories))
                        next = False

                    case "tag":
                        tag = input("tag: ")
                        if tag not in [t.name for t in tags]:
                            session.add([type.Tag(tag)])

                        transaction.tags.add(type.TransactionTag(tag))

                    case "note":
                        note = input("note: ")
                        transaction.note = type.Note(note)

                    case other:
                        if other not in [c.name for c in categories]:
                            print(f"{other} is not a valid category")
                            continue

                        transaction.category = type.TransactionCategory(
                            other,
                            type.CategorySelector(type.Selector_T.manual),
                        )
                        next = False

            session.commit()
            if quit:
                break


def split(
    original: type.Transaction, categories: Sequence[type.Category]
) -> list[type.Transaction]:

    total = original.amount
    splitted: list[type.Transaction] = []

    while True:
        if abs(sum(t.amount for t in splitted)) > abs(total):
            print(
                "The total amount from the splitted transactions exceeds the original transaction amount, please try again..."
            )
            splitted.clear()

        if sum(t.amount for t in splitted) == total:
            break

        while (category := input("New transaction category: ")) not in [
            c.name for c in categories
        ]:
            print(f"{category} is not a valid category")

        amount = input("amount: ")

        split = type.Transaction(original.date, original.description, Decimal(amount))
        split.category = type.TransactionCategory(
            category, type.CategorySelector(type.Selector_T.manual)
        )

        splitted.append(split)

    splitted.insert(0, original)
    return splitted


if __name__ == "__main__":
    argparser = argparser()
    args = vars(argparser.parse_args())

    assert "op" in args, "No Operation selected"
    op: Operation = args.pop("op")

    assert "database" in args, "No database selected"
    db = args.pop("database")

    assert "verbose" in args, "No verbose level specified"
    verbosity = args.pop("verbose")

    params = []
    match (op):
        case Operation.ManualCategorization:
            interactive(Manager(db, verbosity))
            exit()

        case Operation.Parse:
            keys = {"path", "bank", "creditcard"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [args["path"], args["bank"], args["creditcard"]]

        case Operation.RequisitionId:
            keys = {"name", "country"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [args["name"][0], args["country"][0]]

        case Operation.Download:
            keys = {"all", "banks", "interval", "start", "end", "year", "dry_run"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            start, end = parse_args_period(args)
            params = [start, end, args["dry_run"]]

            if not args["all"]:
                params.append(args["banks"])
            else:
                params.append([])

        case Operation.BankAdd:
            keys = {"bank", "bic", "type"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [
                type.Bank(
                    args["bank"][0],
                    args["bic"][0],
                    args["type"][0],
                )
            ]

        case Operation.BankMod:
            keys = {"bank", "bic", "type", "remove"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            nargs_1 = ["bic", "type"]

            param = {"name": args["bank"][0]}
            param |= {k: v[0] for k, v in args.items() if k in nargs_1 and args[k]}
            param |= {k: None for k in args["remove"] if k in nargs_1}

            params = [param]

        case Operation.BankDel:
            assert len(args["bank"]) > 0, "argparser ill defined"
            params = args["bank"]

        case Operation.NordigenAdd:
            keys = {"bank", "bank_id", "requisition_id", "invert"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [
                type.Nordigen(
                    args["bank"][0],
                    args["bank_id"][0] if args["bank_id"] else None,
                    args["requisition_id"][0] if args["requisition_id"] else None,
                    args["invert"] if args["invert"] else None,
                )
            ]

        case Operation.NordigenMod:
            keys = {"bank", "bank_id", "requisition_id", "invert", "remove"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            nargs_1 = ["bank_id", "requisition_id"]
            nargs_0 = ["invert"]

            param = {"name": args["bank"][0]}
            param |= {k: v[0] for k, v in args.items() if k in nargs_1 and args[k]}
            param |= {k: v for k, v in args.items() if k in nargs_0}
            param |= {k: None for k in args["remove"] if k in nargs_1}

            params = [param]

        case Operation.NordigenDel:
            assert len(args["bank"]) > 0, "argparser ill defined"
            params = args["bank"]

        case Operation.NordigenCountryBanks:
            keys = {"country"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [args["country"][0]]

        case Operation.CategoryAdd:
            keys = {"category", "group"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [type.Category(cat, args["group"]) for cat in args["category"]]

        case Operation.CategoryUpdate:
            keys = {"category", "group"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [type.Category(cat) for cat in args["category"]]
            params.append(args["group"])

        case Operation.CategoryRemove:
            assert "category" in args, "argparser ill defined"
            params = [type.Category(cat) for cat in args["category"]]

        case Operation.CategorySchedule:
            keys = {"category", "period", "frequency"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [
                type.CategorySchedule(
                    cat, args["period"][0], args["frequency"][0], None
                )
                for cat in args["category"]
            ]

        case Operation.RuleAdd:
            keys = {"category", "date", "description", "bank", "min", "max"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [
                type.CategoryRule(
                    args["date"][0] if args["date"] else None,
                    args["description"][0] if args["description"] else None,
                    args["regex"][0] if args["regex"] else None,
                    args["bank"][0] if args["bank"] else None,
                    args["min"][0] if args["min"] else None,
                    args["max"][0] if args["max"] else None,
                    cat,
                )
                for cat in args["category"]
            ]

        case Operation.RuleRemove | Operation.TagRuleRemove:
            keys = {"id"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = args["id"]

        case Operation.RuleModify:
            keys = {
                "id",
                "category",
                "date",
                "description",
                "bank",
                "min",
                "max",
                "remove",
            }
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            nargs_1 = ["category", "date", "description", "regex", "bank", "min", "max"]
            params = []
            for id in args["id"]:
                param = {"id": id}
                param |= {k: v[0] for k, v in args.items() if k in nargs_1 and args[k]}
                param |= {k: None for k in args["remove"] if k in nargs_1}

                params.append(param)

        case Operation.TagAdd:
            keys = {"tag"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [type.Tag(tag) for tag in args["tag"]]

        case Operation.TagRuleAdd:
            keys = {"tag", "date", "description", "bank", "min", "max"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [
                type.TagRule(
                    args["date"][0] if args["date"] else None,
                    args["description"][0] if args["description"] else None,
                    args["regex"][0] if args["regex"] else None,
                    args["bank"][0] if args["bank"] else None,
                    args["min"][0] if args["min"] else None,
                    args["max"][0] if args["max"] else None,
                    tag,
                )
                for tag in args["tag"]
            ]

        case Operation.TagRuleModify:
            keys = {"id", "tag", "date", "description", "bank", "min", "max", "remove"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            nargs_1 = ["tag", "date", "description", "regex", "bank", "min", "max"]
            params = []
            for id in args["id"]:
                param = {"id": id}
                param |= {k: v[0] for k, v in args.items() if k in nargs_1 and args[k]}
                param |= {k: None for k in args["remove"] if k in nargs_1}

                params.append(param)

        case Operation.GroupAdd:
            assert "group" in args, "argparser ill defined"
            params = [type.CategoryGroup(group) for group in args["group"]]

        case Operation.GroupRemove:
            assert "group" in args, "argparser ill defined"
            params = [type.CategoryGroup(group) for group in args["group"]]

        case Operation.Forge | Operation.Dismantle:
            keys = {"original", "links"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [type.Link(args["original"][0], link) for link in args["links"]]

        case (
            Operation.Export
            | Operation.Import
            | Operation.ExportBanks
            | Operation.ImportBanks
            | Operation.ExportCategoryRules
            | Operation.ImportCategoryRules
            | Operation.ExportTagRules
            | Operation.ImportTagRules
            | Operation.ExportCategories
            | Operation.ImportCategories
            | Operation.ExportCategoryGroups
            | Operation.ImportCategoryGroups
        ):
            keys = {"file"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = args["file"]

    Manager(db, verbosity).action(op, params)
