package Base_Types is
   type Base_Code is mod 2 ** 16;
   for Base_Code'Size use 16;

   Code_Last_Bit : constant := 15;
   Flag_Last_Bit : constant := 16;
end Base_Types;
