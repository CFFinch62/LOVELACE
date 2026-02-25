with Ada.Text_IO; use Ada.Text_IO;
with Ada.Integer_Text_IO; use Ada.Integer_Text_IO;

procedure Procedures is

   -- A simple procedure
   procedure Greet (Name : String) is
   begin
      Put_Line("Hello, " & Name & "!");
   end Greet;

   -- A function that returns a value
   function Square (N : Integer) return Integer is
   begin
      return N * N;
   end Square;

   Result : Integer;
begin
   Greet("Ada Programmer");
   
   Result := Square(5);
   Put("The square of 5 is ");
   Put(Result, Width => 0);
   New_Line;
end Procedures;
