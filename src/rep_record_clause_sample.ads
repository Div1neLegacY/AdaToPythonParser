with Derived_Types;

package Rep_Record_Clause_Sample is
   type Status_Kind is (Off, On, Error);
   for Status_Kind use
     (Off   => 0,
      On    => 1,
      Error => 2);

   -- Sample 1 --
   type Device_Flags is record
      Enabled : Boolean;
      Ready   : Boolean;
      Mode    : Status_Kind;
   end record;

   -- Representation record clause
   for Device_Flags use record
      Enabled at 0 range 0 .. 0;  -- bit 0
      Ready   at 0 range 1 .. 1;  -- bit 1
      Mode    at 0 range 2 .. Derived_Types.Mode_Last_Bit;  -- bits 2-3
   end record;

   for Device_Flags'Size use 8;

   -- Sample 2 --
   type Packet is record
      Valid : Boolean;
      Error : Boolean;
      Mode  : Derived_Types.Mode_Kind;  -- type from another file
   end record;
   for Packet use record
      Valid at 0 range 0 .. 0;
      Error at 0 range 1 .. 1;
      Mode  at 0 range 2 .. Derived_Types.Mode_Last_Bit;
   end record;
   for Packet'Size use 8;

   -- Sample 3 --
   type Internal_Msg_Payload is record
      Code : Derived_Types.Payload_Code;
      Flag : Boolean;
   end record;

   for Internal_Msg_Payload use record
      Code at 0 range 0 .. Derived_Types.Code_Last_Bit;
      Flag at 0 range 16 .. Derived_Types.Flag_Last_Bit;
   end record;

   -- Sample 4 --
   type Internal_Msg_Payload_Nested is record
      Payload : Internal_Msg_Payload;
   end record;

   for Internal_Msg_Payload_Nested use record
      Payload at 0 range 0 .. Internal_Msg_Payload'Size - 1;
   end record;


end Rep_Record_Clause_Sample;