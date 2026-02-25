# Ada Tutorial — LOVELACE IDE

This tutorial teaches Ada programming using the LOVELACE IDE. By the end you will understand the fundamental building blocks of Ada and be able to write, compile, and run your own programs.

---

## Getting Started

Open LOVELACE (`./run.sh`). Press **`Ctrl+N`** to create a new file, or open one of the bundled examples from the `examples/` folder using the file browser on the left. Press **`Ctrl+R`** to compile and run at any time.

---

## Lesson 1 — Hello, World!

Every programming journey starts here. Type this into a new file and save it as `hello.adb`:

```ada
program Hello;
begin
  WriteLn('Hello, World!');
end.
```

Press `Ctrl+R`. You should see:
```
Hello, World!
```

**What you learned:**
- Every Ada program starts with `program Name;`
- Code runs between `begin` and `end.` (note the final period)
- `WriteLn` prints a line of text and adds a newline

---

## Lesson 2 — Variables and Data Types

Ada is **strongly typed** — every variable has a declared type.

```ada
program Variables;
var
  Name    : String;
  Age     : Integer;
  Height  : Real;
  IsAdult : Boolean;
begin
  Name    := 'Ada Lovelace';
  Age     := 36;
  Height  := 1.68;
  IsAdult := True;

  WriteLn('Name:    ', Name);
  WriteLn('Age:     ', Age);
  WriteLn('Height:  ', Height:4:2, ' m');
  WriteLn('Adult:   ', IsAdult);
end.
```

**Common types:**

| Type      | Example         | Notes                |
| --------- | --------------- | -------------------- |
| `Integer` | `42`            | Whole numbers        |
| `Real`    | `3.14`          | Floating-point       |
| `Char`    | `'A'`           | Single character     |
| `String`  | `'Hello'`       | Text (FPC extension) |
| `Boolean` | `True`, `False` | Logical              |

**Formatted output:** `Height:4:2` means field-width 4, 2 decimal places.

---

## Lesson 3 — Reading Input

```ada
program Greet;
var
  Name : String;
begin
  Write('Enter your name: ');
  ReadLn(Name);
  WriteLn('Hello, ', Name, '!');
end.
```

- `Write` prints without a newline.
- `ReadLn` reads a full line of input into a variable.

---

## Lesson 4 — Conditionals

```ada
program Grade;
var
  Score : Integer;
begin
  Write('Enter score (0-100): ');
  ReadLn(Score);

  if Score >= 90 then
    WriteLn('A — Excellent')
  else if Score >= 80 then
    WriteLn('B — Good')
  else if Score >= 70 then
    WriteLn('C — Satisfactory')
  else
    WriteLn('F — Needs improvement');
end.
```

For multiple values, use `case`:

```ada
case Score div 10 of
  10, 9 : WriteLn('A');
  8     : WriteLn('B');
  7     : WriteLn('C');
  else    WriteLn('F');
end;
```

---

## Lesson 5 — Loops

### `for` loop (counted)
```ada
var i : Integer;
begin
  for i := 1 to 5 do
    WriteLn('Count: ', i);
end.
```

### `while` loop
```ada
var n : Integer;
begin
  n := 1;
  while n <= 10 do
  begin
    WriteLn(n);
    Inc(n);  { same as n := n + 1 }
  end;
end.
```

### `repeat…until` loop
```ada
var x : Integer;
begin
  x := 0;
  repeat
    Inc(x);
    WriteLn(x);
  until x >= 5;
end.
```

> **Note:** Use `begin…end` when a loop body has more than one statement.

---

## Lesson 6 — Procedures and Functions

```ada
program MathDemo;

{ A procedure performs an action }
procedure Greet(const Name : String);
begin
  WriteLn('Hello, ', Name, '!');
end;

{ A function returns a value }
function Square(n : Integer) : Integer;
begin
  Square := n * n;
end;

{ Recursive function }
function Factorial(n : Integer) : Integer;
begin
  if n <= 1 then
    Factorial := 1
  else
    Factorial := n * Factorial(n - 1);
end;

begin
  Greet('Grace');
  WriteLn('5 squared = ', Square(5));
  WriteLn('6! = ', Factorial(6));
end.
```

**Parameter modes:**
- `const` — read-only, passed efficiently
- `var` — passed by reference (changes affect the caller)
- (none) — passed by value (copy)

---

## Lesson 7 — Arrays

```ada
program Arrays;
const
  N = 5;
var
  Scores : array[1..N] of Integer;
  i, Total : Integer;
begin
  for i := 1 to N do
    Scores[i] := i * 10;

  Total := 0;
  for i := 1 to N do
    Total := Total + Scores[i];

  WriteLn('Sum = ', Total);
  WriteLn('Avg = ', Total / N : 0 : 1);
end.
```

---

## Lesson 8 — Records

Records group related data:

```ada
program RecordDemo;
type
  TPerson = record
    Name  : String[30];
    Age   : Integer;
  end;

var
  P : TPerson;
begin
  P.Name := 'Grace Hopper';
  P.Age  := 85;
  WriteLn(P.Name, ' — Age: ', P.Age);
end.
```

---

## Lesson 9 — File I/O

```ada
program FileDemo;
var
  F    : TextFile;
  Line : String;
begin
  { Write }
  AssignFile(F, 'output.txt');
  Rewrite(F);
  WriteLn(F, 'Hello from Ada!');
  CloseFile(F);

  { Read }
  Reset(F);
  while not EOF(F) do
  begin
    ReadLn(F, Line);
    WriteLn(Line);
  end;
  CloseFile(F);
end.
```

---

## Next Steps

- Browse the `examples/` folder in LOVELACE for more programs.
- Read the [Ada Language Reference](LANGUAGE-REFERENCE.md) for a complete keyword listing.
- Try combining procedures, loops, and records to build a simple contact book.
