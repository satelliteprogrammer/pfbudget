import pfbudget


if __name__ == "__main__":
    argparser = pfbudget.argparser()
    args = vars(argparser.parse_args())

    assert "op" in args, "No pfbudget.Operation selected"
    op: pfbudget.Operation = args.pop("op")

    assert "database" in args, "No database selected"
    db = args.pop("database")

    assert "verbose" in args, "No verbose level specified"
    verbosity = args.pop("verbose")

    params = None
    match (op):
        case pfbudget.Operation.Parse:
            keys = {"path", "bank", "creditcard"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [args["path"], args["bank"], args["creditcard"]]

        case pfbudget.Operation.RequisitionId:
            keys = {"name", "country"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [args["name"][0], args["country"][0]]

        case pfbudget.Operation.Download:
            keys = {"all", "banks", "interval", "start", "end", "year", "dry_run"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            start, end = pfbudget.parse_args_period(args)
            params = [start, end, args["dry_run"]]

            if not args["all"]:
                params.append(args["banks"])
            else:
                params.append([])

        case pfbudget.Operation.BankAdd:
            keys = {"bank", "bic", "type"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [
                pfbudget.types.Bank(
                    args["bank"][0],
                    args["bic"][0],
                    args["type"][0],
                )
            ]

        case pfbudget.Operation.BankMod:
            keys = {"bank", "bic", "type", "remove"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            nargs_1 = ["bic", "type"]

            param = {"name": args["bank"][0]}
            param |= {k: v[0] for k, v in args.items() if k in nargs_1 and args[k]}
            param |= {k: None for k in args["remove"] if k in nargs_1}

            params = [param]

        case pfbudget.Operation.BankDel:
            assert len(args["bank"]) > 0, "argparser ill defined"
            params = args["bank"]

        case pfbudget.Operation.NordigenAdd:
            keys = {"bank", "bank_id", "requisition_id", "invert"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [
                pfbudget.types.Nordigen(
                    args["bank"][0],
                    args["bank_id"][0] if args["bank_id"] else None,
                    args["requisition_id"][0] if args["requisition_id"] else None,
                    args["invert"] if args["invert"] else None,
                )
            ]

        case pfbudget.Operation.NordigenMod:
            keys = {"bank", "bank_id", "requisition_id", "invert", "remove"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            nargs_1 = ["bank_id", "requisition_id"]
            nargs_0 = ["invert"]

            param = {"name": args["bank"][0]}
            param |= {k: v[0] for k, v in args.items() if k in nargs_1 and args[k]}
            param |= {k: v for k, v in args.items() if k in nargs_0}
            param |= {k: None for k in args["remove"] if k in nargs_1}

            params = [param]

        case pfbudget.Operation.NordigenDel:
            assert len(args["bank"]) > 0, "argparser ill defined"
            params = args["bank"]

        case pfbudget.Operation.NordigenCountryBanks:
            keys = {"country"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [args["country"][0]]

        case pfbudget.Operation.CategoryAdd:
            keys = {"category", "group"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [
                pfbudget.types.Category(cat, args["group"]) for cat in args["category"]
            ]

        case pfbudget.Operation.CategoryUpdate:
            keys = {"category", "group"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [pfbudget.types.Category(cat) for cat in args["category"]]
            params.append(args["group"])

        case pfbudget.Operation.CategoryRemove:
            assert "category" in args, "argparser ill defined"
            params = [pfbudget.types.Category(cat) for cat in args["category"]]

        case pfbudget.Operation.CategorySchedule:
            keys = {"category", "period", "frequency"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [
                pfbudget.types.CategorySchedule(
                    cat, True, args["period"][0], args["frequency"][0]
                )
                for cat in args["category"]
            ]

        case pfbudget.Operation.RuleAdd:
            keys = {"category", "date", "description", "bank", "min", "max"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [
                pfbudget.types.CategoryRule(
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

        case pfbudget.Operation.RuleRemove | pfbudget.Operation.TagRuleRemove:
            keys = {"id"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = args["id"]

        case pfbudget.Operation.RuleModify:
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

        case pfbudget.Operation.TagAdd:
            keys = {"tag"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [pfbudget.types.Tag(tag) for tag in args["tag"]]

        case pfbudget.Operation.TagRuleAdd:
            keys = {"tag", "date", "description", "bank", "min", "max"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [
                pfbudget.types.TagRule(
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

        case pfbudget.Operation.TagRuleModify:
            keys = {"id", "tag", "date", "description", "bank", "min", "max", "remove"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            nargs_1 = ["tag", "date", "description", "regex", "bank", "min", "max"]
            params = []
            for id in args["id"]:
                param = {"id": id}
                param |= {k: v[0] for k, v in args.items() if k in nargs_1 and args[k]}
                param |= {k: None for k in args["remove"] if k in nargs_1}

                params.append(param)

        case pfbudget.Operation.GroupAdd:
            assert "group" in args, "argparser ill defined"
            params = [pfbudget.types.CategoryGroup(group) for group in args["group"]]

        case pfbudget.Operation.GroupRemove:
            assert "group" in args, "argparser ill defined"
            params = [pfbudget.types.CategoryGroup(group) for group in args["group"]]

        case pfbudget.Operation.Forge | pfbudget.Operation.Dismantle:
            keys = {"original", "links"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            params = [
                pfbudget.types.Link(args["original"][0], link) for link in args["links"]
            ]

        case pfbudget.Operation.Export:
            keys = {"interval", "start", "end", "year", "all", "banks", "file"}
            assert args.keys() >= keys, f"missing {args.keys() - keys}"

            start, end = pfbudget.parse_args_period(args)
            params = [start, end]
            if not args["all"]:
                params.append(args["banks"])
            params.append(args["file"][0])

    pfbudget.Manager(db, verbosity).action(op, params)
