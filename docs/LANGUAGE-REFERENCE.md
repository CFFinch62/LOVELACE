# Ada Language Reference — LOVELACE IDE

A concise reference for the Free Ada language as used in the LOVELACE IDE.

---

## Program Structure

```ada
program ProgramName;
uses SysUtils, Classes;   { Optional unit imports }

const
  PI = 3.14159;

type
  TMyRecord = record ... end;

var
  x : Integer;

{ Procedures and functions here }

begin
  { Main body }
end.
```

---

## Data Types

### Ordinal Types
| Type                  | Range            | Size    |
| --------------------- | ---------------- | ------- |
| `Byte`                | 0–255            | 1 byte  |
| `ShortInt`            | −128–127         | 1 byte  |
| `SmallInt`            | −32768–32767     | 2 bytes |
| `Word`                | 0–65535          | 2 bytes |
| `Integer`             | −2³¹–2³¹−1       | 4 bytes |
| `LongWord`/`Cardinal` | 0–2³²−1          | 4 bytes |
| `Int64`               | −2⁶³–2⁶³−1       | 8 bytes |
| `Char`                | Single character | 1 byte  |
| `Boolean`             | `True`, `False`  | 1 byte  |

### Real Types
| Type       | Precision    | Range                       |
| ---------- | ------------ | --------------------------- |
| `Single`   | 7 digits     | ±1.5×10⁻⁴⁵ – ±3.4×10³⁸      |
| `Double`   | 15 digits    | ±5×10⁻³²⁴ – ±1.7×10³⁰⁸      |
| `Extended` | 18–19 digits | 80-bit (platform-dependent) |
| `Real`     | 15 digits    | Alias for `Double` in FPC   |

### String Types
| Type         | Notes                                   |
| ------------ | --------------------------------------- |
| `String`     | Dynamic string (FPC extension, default) |
| `String[N]`  | Short string, max N chars               |
| `AnsiString` | Reference-counted, long string          |
| `PChar`      | Null-terminated C-style string          |

### Structured Types
```ada
{ Array }
array[1..10] of Integer
array[Char] of Boolean                { Using ordinal index }

{ Record }
type TPerson = record
  Name : String;
  Age  : Integer;
end;

{ Set }
type TDigit = set of '0'..'9';

{ Pointer }
var P : ^Integer;
New(P);  P^ := 42;  Dispose(P);
```

---

## Constants and Enumerations

```ada
const
  MaxSize = 100;             { Typed constant }
  E : Double = 2.71828;     { Typed constant with type }

type
  TColor = (Red, Green, Blue);
  TCardRank = (Two, Three, Four, Five, Six, Seven, Eight,
               Nine, Ten, Jack, Queen, King, Ace);
```

---

## Operators

### Arithmetic
| Operator    | Operation               |
| ----------- | ----------------------- |
| `+` `-` `*` | Add, subtract, multiply |
| `/`         | Real division           |
| `div`       | Integer division        |
| `mod`       | Modulo remainder        |

### Comparison
`=`  `<>`  `<`  `>`  `<=`  `>=`

### Logical
`and`  `or`  `not`  `xor`

### String
`+` — concatenation

---

## Control Flow

### Conditionals
```ada
if condition then
  statement
else if condition then
  statement
else
  statement;

case variable of
  value1 : statement;
  value2, value3 : statement;
  else statement;
end;
```

### Loops
```ada
for i := low to high do statement;
for i := high downto low do statement;

while condition do statement;

repeat
  statements;
until condition;

{ Exit loops early }
Break;    { exit the loop }
Continue; { skip to next iteration }
```

### Exception Handling
```ada
try
  RiskyOperation;
except
  on E: EInOutError do WriteLn('I/O Error: ', E.Message);
  on E: Exception    do WriteLn('Error: ', E.Message);
end;

try
  RiskyOperation;
finally
  CleanUp;  { always runs }
end;
```

---

## Procedures and Functions

```ada
{ Procedure — no return value }
procedure PrintLine(const S : String);
begin
  WriteLn(S);
end;

{ Function — returns a value }
function Add(A, B : Integer) : Integer;
begin
  Add := A + B;      { or: Result := A + B; }
end;

{ var parameter — passed by reference }
procedure Swap(var A, B : Integer);
var Temp : Integer;
begin
  Temp := A; A := B; B := Temp;
end;

{ Overloading (FPC extension) }
function Max(A, B : Integer) : Integer; overload;
function Max(A, B : Double) : Double;   overload;
```

---

## Standard I/O

```ada
Write('prompt: ');          { Print without newline }
WriteLn('Hello');           { Print with newline }
WriteLn(x : 8 : 2);        { Field-width 8, 2 decimal places }

ReadLn(x);                  { Read and consume newline }
Read(ch);                   { Read without consuming newline }
```

---

## File I/O

```ada
var F : TextFile;

{ Write }
AssignFile(F, 'out.txt');
Rewrite(F);                 { Create/overwrite }
WriteLn(F, 'Line 1');
CloseFile(F);

{ Append }
Append(F);
WriteLn(F, 'New line');
CloseFile(F);

{ Read }
Reset(F);                   { Open for reading }
while not EOF(F) do
begin
  ReadLn(F, Line);
  WriteLn(Line);
end;
CloseFile(F);
```

---

## Key Standard Routines

### Math
| Routine                    | Description                  |
| -------------------------- | ---------------------------- |
| `Abs(x)`                   | Absolute value               |
| `Sqr(x)`                   | Square (x²)                  |
| `Sqrt(x)`                  | Square root                  |
| `Round(x)`                 | Round to nearest integer     |
| `Trunc(x)`                 | Truncate to integer          |
| `Int(x)`                   | Integer part as Real         |
| `Odd(n)`                   | True if n is odd             |
| `Power(base, exp)`         | Exponentiation (`Math` unit) |
| `Sin(x)` `Cos(x)` `Tan(x)` | Trig functions (radians)     |
| `Ln(x)` `Exp(x)`           | Natural log / exponential    |

### String Routines
| Routine               | Description                    |
| --------------------- | ------------------------------ |
| `Length(s)`           | Length of string               |
| `Copy(s, pos, len)`   | Extract substring              |
| `Pos(sub, s)`         | Find position of sub in s      |
| `Concat(s1, s2, ...)` | Concatenate strings            |
| `Delete(s, pos, len)` | Delete characters in-place     |
| `Insert(sub, s, pos)` | Insert string in-place         |
| `UpperCase(s)`        | Convert to uppercase           |
| `LowerCase(s)`        | Convert to lowercase           |
| `Trim(s)`             | Remove leading/trailing spaces |
| `IntToStr(n)`         | Integer → String               |
| `StrToInt(s)`         | String → Integer               |
| `FloatToStr(f)`       | Real → String                  |
| `StrToFloat(s)`       | String → Real                  |

### Memory and Misc
| Routine               | Description                      |
| --------------------- | -------------------------------- |
| `New(ptr)`            | Allocate pointer                 |
| `Dispose(ptr)`        | Free pointer                     |
| `Inc(n)` / `Dec(n)`   | Increment/decrement              |
| `Succ(x)` / `Pred(x)` | Next/previous ordinal value      |
| `Ord(ch)`             | Ordinal value of character       |
| `Chr(n)`              | Character from ordinal           |
| `Halt(code)`          | Terminate program with exit code |

---

## Compiler Directives (gnatmake)

```ada
{$mode objgnatmake}    { ObjFPC mode (OOP enabled) }
{$H+}             { Use long strings (AnsiString) }
{$R+}             { Range checking }
{$I-}             { Disable I/O checking }
{$define MY_FLAG} { Define a compiler symbol }
{$ifdef MY_FLAG}  { Conditional compilation }
  ...
{$endif}
```

---

## Units (common)

| Unit       | Contents                                      |
| ---------- | --------------------------------------------- |
| `System`   | Auto-included: I/O, strings, memory           |
| `SysUtils` | String conversion, exceptions, file utilities |
| `Math`     | Extended math: `Power`, trig, `IsNaN`, etc.   |
| `Classes`  | `TStringList`, `TStream`, `TComponent`        |
| `StrUtils` | `PadLeft`, `ReverseString`, `AnsiContainsStr` |

---

*Free Ada documentation: [freeada.org/docs.html](https://freeada.org/docs.html)*
