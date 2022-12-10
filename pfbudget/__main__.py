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
                pfbudget.types.Category(cat, args["group"][0])
                for cat in args["category"]
            ]

        case pfbudget.Operation.CategoryUpdate:
            assert args.keys() >= {"category", "group"}, "argparser ill defined"
            params = [pfbudget.types.Category(cat) for cat in args["category"]]
            params.append(args["group"][0])

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

        case pfbudget.Operation.GroupAdd:
            assert "group" in args, "argparser ill defined"
            params = [pfbudget.types.CategoryGroup(group) for group in args["group"]]

        case pfbudget.Operation.GroupRemove:
            assert "group" in args, "argparser ill defined"
            params = [pfbudget.types.CategoryGroup(group) for group in args["group"]]

    pfbudget.Manager(db, args).action(op, params)
