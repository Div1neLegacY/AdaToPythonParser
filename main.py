import ada_parser

def main():
    print("Hello, World!")

    # Sample record #1
    ada_record = ada_parser.get_record_rep_clause("src/rep_record_clause_sample.ads", "Device_Flags")
    print(f"Found Ada record: {ada_record}")

    # Sample record #2
    ada_record = ada_parser.get_record_rep_clause("src/rep_record_clause_sample.ads", "Packet")
    print(f"Found Ada record: {ada_record}")

    # Sample record #3
    ada_record = ada_parser.get_record_rep_clause("src/rep_record_clause_sample.ads", "Internal_Msg_Payload")
    print(f"Found Ada record: {ada_record}")

    # Sample record #4 (Nested Record)
    ada_record = ada_parser.get_record_rep_clause("src/rep_record_clause_sample.ads", "Internal_Msg_Payload_Nested")
    print(f"Found Ada record: {ada_record}")

if __name__ == "__main__":
    main()
