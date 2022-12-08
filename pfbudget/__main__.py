import pfbudget


if __name__ == "__main__":
    argparser = pfbudget.argparser()
    args = vars(argparser.parse_args())
    assert "op" in args, "No operation selected"
    pfbudget.Manager(args["op"], args).start()
