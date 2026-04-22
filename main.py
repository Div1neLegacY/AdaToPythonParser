import ada_parser

def main():
    print("Hello, World!")
    ada_record = (None, [])
    ada_record = ada_parser.get_record_rep_clause("msg_payloads.adb", "Internal_Msg_Payload")
    print(f"Found Ada record: {ada_record}")

if __name__ == "__main__":
    main()