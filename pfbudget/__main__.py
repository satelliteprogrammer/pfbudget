import pfbudget


if __name__ == "__main__":
    argparser = pfbudget.argparser()
    args = vars(argparser.parse_args())

    assert "op" in args, "No pfbudget.Operation selected"
    op: pfbudget.Operation = args["op"]

    assert "database" in args, "No database selected"
    db = args["database"]

    params = None
    match (op):
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
                    cat,
                    args["date"][0] if args["date"] else None,
                    args["description"][0] if args["description"] else None,
                    args["regex"][0] if args["regex"] else None,
                    args["bank"][0] if args["bank"] else None,
                    args["min"][0] if args["min"] else None,
                    args["max"][0] if args["max"] else None,
                )
                for cat in args["category"]
            ]

        case pfbudget.Operation.RuleRemove:
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

        case pfbudget.Operation.GroupAdd:
            assert "group" in args, "argparser ill defined"
            params = [pfbudget.types.CategoryGroup(group) for group in args["group"]]

        case pfbudget.Operation.GroupRemove:
            assert "group" in args, "argparser ill defined"
            params = [pfbudget.types.CategoryGroup(group) for group in args["group"]]

    pfbudget.Manager(db, args).action(op, params)
