# Report for Assignment 1

## Project chosen

Name: SimpleParsing

URL: https://github.com/lebrice/SimpleParsing

Number of lines of code and the tool used to count it: lizard, 18161 nloc

Programming language: Python

## Coverage measurement

### Existing tool

Coverage.py via the command: coverage run -m pytest

![image](https://github.com/noracai26/SimpleParsing/assets/76873802/8d8e2c1e-9066-43c6-b77f-f3e3a1a953c4)


### Your own coverage tool

<The following is supposed to be repeated for each group member>

<Group member name> Karina Sudnicina

Function 1 name: get_bound(t) from simple_parsing/utils.py

![image](https://github.com/noracai26/SimpleParsing/assets/76873802/359c53f7-65f6-42f9-a90b-c7386723108f)


Function 2 name: _description_from_docstring(docstring: dp.Docstring) from simple_parsing/decorators.py

![image](https://github.com/noracai26/SimpleParsing/assets/76873802/d43a7a5b-f63d-4435-948e-5dceabd67bf2)

<br>

<Group member name>Nora Cai

Function 1 name: def __post_init__ from examples/ugly_example_after.py


![77EEF328-316B-4EC1-8183-7A21D9A2FEFC_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/4a7991f0-7bee-4119-9b57-ea2a1272c192)


![D44E1447-744E-4E90-9AB9-66AD85D8B659_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/6d2dc978-f224-43af-9ec5-1e5640ca720a)


Function 2 name: def contains_dataclass_type_arg from simple_parsing/utils.py

![15C6B39A-F85B-40D7-868A-BD7814146D84_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/d2762aaa-7c95-482d-ba27-7cb13ed9e99d)

![A5692BBC-EAA6-45F5-AE32-596AAD60B2AC_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/4176aeb4-b232-42be-9ef4-db9332c05861)


<br>

<Group member name>

<Function 1 name>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the instrumented code to gather coverage measurements>

<Provide a screenshot of the coverage results output by the instrumentation>

<Function 2 name>

<Provide the same kind of information provided for Function 1>
<br>

<Group member name>

<Function 1 name>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the instrumented code to gather coverage measurements>

<Provide a screenshot of the coverage results output by the instrumentation>

<Function 2 name>

<Provide the same kind of information provided for Function 1>
<br>

## Coverage improvement

### Individual tests

<The following is supposed to be repeated for each group member>

<Group member name> Karina Sudnicina

Test 1: get_bound(t)

Coverage before: <br>![get_bound without tests](https://github.com/noracai26/SimpleParsing/assets/76873802/f370b19e-382e-4de3-bb8b-1c51e5645143)<br>
Coverage after: <br> ![get_bound with tests](https://github.com/noracai26/SimpleParsing/assets/76873802/de09d705-46b9-448c-b2a0-4ff9d19eb5c0)


<State the coverage improvement with a number and elaborate on why the coverage is improved>
As seen from the screenshot, the function was initially not covered completely by test cases. I have added the test cases to make sure all of the brances are covered. As a result, the function is covered by 100%
and the number of 'missing' statements in utils.py got decreased by 1 - from 77 to 76.

<br><br>

Test 2: def _description_from_docstring(docstring: dp.Docstring)

Coverage before: <br> ![description_from_docstring_before](https://github.com/noracai26/SimpleParsing/assets/76873802/070a6577-33d7-4159-af7f-2f35631175da)
Coverage after: <br>![description_from_docstring_after](https://github.com/noracai26/SimpleParsing/assets/76873802/d51ca4b7-f9d7-4970-9623-e3aa70e3ad1e)

<State the coverage improvement with a number and elaborate on why the coverage is improved>
Similarly, the function was not covered completely. Adding new test cases for this function raised the coverage of decorators.py file for 2% - from 91 to 93. The function is now covered by 100% and the 'missing' statements number has also decreased by 1 - from 6 to 5. 

<br><br>
<Group member name> Nora Cai

Test 1: test/test_ugly_example_after.py

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>

<Test 2>

<Provide the same kind of information provided for Test 1>


<br>
<Group member name>

<Test 1>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>

<Test 2>

<Provide the same kind of information provided for Test 1>


<br>
<Group member name>

<Test 1>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>

<Test 2>

<Provide the same kind of information provided for Test 1>

### Overall

Old result:

![image](https://github.com/noracai26/SimpleParsing/assets/76873802/8d8e2c1e-9066-43c6-b77f-f3e3a1a953c4)

<Provide a screenshot of the new coverage results by running the existing tool using all test modifications made by the group>
New result:

![5203FD40-78B8-4387-8AA3-2DEED960CAD5_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/d9827642-a80c-4005-af8a-5082ed2dfaac)

## Statement of individual contributions


<Write what each group member did>
Karina Sudnicina: found the project, implemented coverage tool for two functions mentioned above, created a test cases for them.
