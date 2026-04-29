with Base_Types;

package Derived_Types is
   type Mode_Kind is (Idle, Run, Fault);
   for Mode_Kind use
     (Idle  => 0,
      Run   => 1,
      Fault => 2);

   Mode_Last_Bit : constant := 3;

   type Payload_Code is new Base_Types.Base_Code;
   Code_Last_Bit : constant Payload_Code := Payload_Code (Base_Types.Code_Last_Bit);
   Flag_Last_Bit : constant Payload_Code := Payload_Code (Base_Types.Flag_Last_Bit);
end Derived_Types;
