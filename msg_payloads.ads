package Msg_Payloads is

   type Msg_ID is new Natural range 1 .. 10;
   for Msg_ID'Size use 32;

end Msg_Payloads;