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
        case pfbudget.Operation.RequisitionId:
            assert args.keys() >= {"name", "country"}, "argparser ill defined"
            params = [args["name"][0], args["country"][0]]

        case pfbudget.Operation.Download:
            assert args.keys() >= {
                "id",
                "name",
                "all",
                "interval",
                "start",
                "end",
                "year",
            }, "argparser ill defined"
            start, end = pfbudget.parse_args_period(args)
            params = [start, end]

        case pfbudget.Operation.BankAdd:
            assert args.keys() >= {
                "bank",
                "bic",
                "type",
            }, "argparser ill defined"

            params = [
                pfbudget.types.Bank(
                    args["bank"][0],
                    args["bic"][0],
                    args["type"][0],
                )
            ]

        case pfbudget.Operation.BankMod:
            assert args.keys() >= {
                "bank",
                "bic",
                "type",
                "remove",
            }, "argparser ill defined"

            nargs_1 = ["bic", "type"]

            param = {"name": args["bank"][0]}
            param |= {k: v[0] for k, v in args.items() if k in nargs_1 and args[k]}
            param |= {k: None for k in args["remove"] if k in nargs_1}

            params = [param]

        case pfbudget.Operation.BankDel:
            assert len(args["bank"]) > 0, "argparser ill defined"
            params = args["bank"]

        case pfbudget.Operation.NordigenAdd:
            assert args.keys() >= {
                "bank",
                "bank_id",
                "requisition_id",
                "invert",
            }, "argparser ill defined"

            params = [
                pfbudget.types.Nordigen(
                    args["bank"][0],
                    args["bank_id"][0] if args["bank_id"] else None,
                    args["requisition_id"][0] if args["requisition_id"] else None,
                    args["invert"] if args["invert"] else None,
                )
            ]

        case pfbudget.Operation.NordigenMod:
            assert args.keys() >= {
                "bank",
                "bank_id",
                "requisition_id",
                "invert",
                "remove",
            }, "argparser ill defined"

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

        case pfbudget.Operation.CategoryAdd:
            assert args.keys() >= {"category", "group"}, "argparser ill defined"
            params = [
                pfbudget.types.Category(cat, args["group"]) for cat in args["category"]
            ]

        case pfbudget.Operation.CategoryUpdate:
            assert args.keys() >= {"category", "group"}, "argparser ill defined"
            params = [pfbudget.types.Category(cat) for cat in args["category"]]
            params.append(args["group"])

        case pfbudget.Operation.CategoryRemove:
            assert "category" in args, "argparser ill defined"
            params = [pfbudget.types.Category(cat) for cat in args["category"]]

        case pfbudget.Operation.CategorySchedule:
            assert args.keys() >= {
                "category",
                "period",
                "frequency",
            }, "argparser ill defined"

            params = [
                pfbudget.types.CategorySchedule(
                    cat, True, args["period"][0], args["frequency"][0]
                )
                for cat in args["category"]
            ]

        case pfbudget.Operation.RuleAdd:
            assert args.keys() >= {
                "category",
                "date",
                "description",
                "bank",
                "min",
                "max",
            }, "argparser ill defined"

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
            assert args.keys() >= {"id"}, "argparser ill defined"
            params = args["id"]

        case pfbudget.Operation.RuleModify:
            assert args.keys() >= {
                "id",
                "category",
                "date",
                "description",
                "bank",
                "min",
                "max",
                "remove",
            }, "argparser ill defined"

            nargs_1 = ["category", "date", "description", "regex", "bank", "min", "max"]
            params = []
            for id in args["id"]:
                param = {"id": id}
                param |= {k: v[0] for k, v in args.items() if k in nargs_1 and args[k]}
                param |= {k: None for k in args["remove"] if k in nargs_1}

                params.append(param)

        case pfbudget.Operation.TagAdd:
            assert args.keys() >= {"tag"}, "argparser ill defined"
            params = [pfbudget.types.Tag(tag) for tag in args["tag"]]

        case pfbudget.Operation.TagRuleAdd:
            assert args.keys() >= {
                "tag",
                "date",
                "description",
                "bank",
                "min",
                "max",
            }, "argparser ill defined"

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
            assert args.keys() >= {
                "id",
                "tag",
                "date",
                "description",
                "bank",
                "min",
                "max",
                "remove",
            }, "argparser ill defined"

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
            assert args.keys() >= {"original", "links"}, "argparser ill defined"
            params = [
                pfbudget.types.Link(args["original"][0], link) for link in args["links"]
            ]

    pfbudget.Manager(db, verbosity, args).action(op, params)
