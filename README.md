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

![15C6B39A-F85B-40D7-868A-BD7814146D84_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/e1e013fd-8147-46ec-a2c4-ae574826d108)

![D44E1447-744E-4E90-9AB9-66AD85D8B659_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/6d2dc978-f224-43af-9ec5-1e5640ca720a)


Function 2 name: def contains_dataclass_type_arg from simple_parsing/utils.py

![15C6B39A-F85B-40D7-868A-BD7814146D84_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/d2762aaa-7c95-482d-ba27-7cb13ed9e99d)

![A5692BBC-EAA6-45F5-AE32-596AAD60B2AC_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/4176aeb4-b232-42be-9ef4-db9332c05861)


<br>

<Group member name> Che Lai

Function 1 name: def setattr_recursive from simple_parsing/utils.py

![3891718737517_ pic](https://github.com/noracai26/SimpleParsing/assets/135572774/5104306a-3df1-4fa2-927e-66185f03c6af)

![3841718649695_ pic](https://github.com/noracai26/SimpleParsing/assets/135572774/709ec3c8-3a38-4168-a196-c7810c918069)


<Function 2 name> def getattr_recursive from simple_parsing/utils.py

![3901718737537_ pic](https://github.com/noracai26/SimpleParsing/assets/135572774/953f9db4-611b-459a-9aa1-f3b77f17e2e5)

![3841718649695_ pic](https://github.com/noracai26/SimpleParsing/assets/135572774/cfdb6903-50a1-443c-a395-0da800c54ded)

<br>

<Group member name> Sanne Aerts

The global variable branch_coverage tracks coverage, and the print_coverage() function prints the results.
This function is called in config.py after all tests have been run with pytest.
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/316afcc2-ffd0-4bd3-b71e-4358d182efb8)

Function 1: get_item_type from simple_parsing/utils.py

The instrumented function
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/c44eb8a2-d2b4-40c8-b0f8-c8ead9ad758b)

Coverage results output from the instrumentation
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/0b738d01-ac1f-4885-b206-14c8c21bc4de)

Function 2: get_argparse_type_for_container from simple_parsing/utils.py

The instrumented function
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/fb502335-2e13-4033-91b6-12b77801540c)

Coverage results output from the instrumentation
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/788bd88d-6aa9-409b-b90c-e8d03d49d47c)

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

added new test:

![DE6C58C0-C52B-40B5-8FB7-492B1ADDBE97](https://github.com/noracai26/SimpleParsing/assets/90709657/f3426fad-cc8a-4bc4-a75b-27b32d08ed2b)

old coverage:

![A3D1D742-6072-4379-B4FC-7C709D595299_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/e6cfaa8f-872e-4aa3-9f6f-30bb594a7b9e)

new coverage:

![77EEF328-316B-4EC1-8183-7A21D9A2FEFC_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/becd7012-22c0-42e7-866e-25602b565370)


percentage of improvement: 60%%

![9CFFF73C-F44B-43ED-A9A1-A718B839F63F_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/96de4555-657d-439c-8fbb-06b823331d98)

![0BE40E06-0EC0-4DB6-BD22-32BBABD08BD1_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/a60375d4-06b6-4b8d-9f35-90fc5b08221b)

The coverage of the function def __post_init__ went from 40% to 100%, this is because the coverage for the function has been improved by writing test case to cover the second and third branch, which were not previously covered.

Test 2: test/test_base.py

enhanced existing test:

![00CC657A-5AB9-4523-ADE5-21180F44985F](https://github.com/noracai26/SimpleParsing/assets/90709657/be69a8f0-4fed-4e74-bb40-f660ffdf5b06)

old coverage:

![AB405694-D254-4802-8724-270B2223A4C7_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/1347cb1a-c3f7-4d18-a8a4-611135590f78)

new coverage:

![B76F7C5B-6034-4358-B9F4-A651EDDD191A_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/05b8b551-bd36-45a9-9479-6728d3f0d7f5)

percentage of improvement: 14%

![31650BE9-DBBD-426C-96AC-FE910953B826_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/efb040fe-a02a-4032-9f14-5f8c19508dda)

![EE3DB7E3-22FD-4476-8F6D-EAD10AAFF1D4_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/ce548844-db5c-4c75-a56a-18b330079363)

The coverage of the function def contains_dataclass_type_arg went from 86% to 100%, the increase is caused by the enhancement of test cases that that covers the second branch of the function, which was not previously covered.



<br>
<Group member name> Che Lai

<Test 1> setattr_recursive

old coverage results: (coverage: 0%)
![3871718651183_ pic](https://github.com/noracai26/SimpleParsing/assets/135572774/2b43ac8b-5a4d-4378-9e12-e01319eb5d4b)

![3851718651108_ pic](https://github.com/noracai26/SimpleParsing/assets/135572774/956ab807-ae39-44b5-9ecd-2a674e46532d)

new coverage results: (coverage: 100%)
![3971718738756_ pic](https://github.com/noracai26/SimpleParsing/assets/135572774/d963d989-38c4-4bc7-8d8e-1f53a07c5611)

![3941718738557_ pic](https://github.com/noracai26/SimpleParsing/assets/135572774/c73e5dc7-221e-4e17-8ec3-cee18198b196)


In the original test file, there was no test case for this function, so the coverage of this function was 0%, then I added the test code for this function, then its coverage increased to 100%.

<Test 2> getattr_recursive

old coverage results: (coverage: 0%)

![3931718738438_ pic](https://github.com/noracai26/SimpleParsing/assets/135572774/4851b8b1-a9fb-4604-8334-8185e3c12b5f)

![3861718651118_ pic](https://github.com/noracai26/SimpleParsing/assets/135572774/82439748-14d1-48a2-ad50-023f24244c03)

new coverage results: (coverage: 100%)
![3961718738689_ pic](https://github.com/noracai26/SimpleParsing/assets/135572774/d8206ed6-5563-44a6-a2c6-259bd2d00991)

![3951718738569_ pic](https://github.com/noracai26/SimpleParsing/assets/135572774/76446167-4e04-4a67-b975-c0179c213bd4)

percentage of improvement: 100%

Same as the function in Test 1, there was no test case for this function, so the old covearage was 0%, after I added test case for it, the coverage of this function increased to 100%.

<br>
<Group member name> Sanne Aerts

Test 1: New test for Function 1 (get_item_type from simple_parsing/utils.py) to hit the third branch.
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/03b45af5-dd3a-41c0-bd72-566bd9430794)

Old coverage result
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/3f7a3126-05c2-439e-9bed-88d7a2a0bb81)
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/9ec037bf-9096-46e8-a508-961a77f07350)
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/f7b12ff4-5cae-4027-8b19-db0ed54d30bc)

New coverage result
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/091bc99f-24cf-41d8-a14c-5f434c4ab9b5)
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/c289eb4e-2a58-41ee-a5e7-af9c4cd240c6)
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/781c7ec8-a37d-463a-8c53-5c7eab5e207a)

Adding a new test case to cover the third branch of the function resulted in a coverage improvement of 17%, bringing the total coverage for the function to 100%.
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/c31ffb75-8ed4-473b-9fb0-ed41178f10c7)
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/5d8258b0-8c6d-4a05-ace3-e5c9ffe47fa5)

Test 2: New test for Function 2 (get_argparse_type_for_container from simple_parsing/utils.py) to hit the second branch.

Old coverage result
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/c8937278-2d74-4f60-960d-12c64d1acf81)
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/04bdf961-804b-47d1-8541-f73251d1f05f)
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/4fccb159-a9f6-48b7-ab7a-79a02523bff7)


New coverage result
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/2b01269e-6e59-4f14-98ac-2a9914cad684)
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/0dae13eb-c835-48d3-808d-58b402383b16)
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/a0f86a2f-66b1-4f63-85d1-7fa1c4feccd9)

Adding a new test case to cover the second branch of the function resulted in a coverage improvement of 11%, bringing the total coverage for the function to 100%.
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/d1dcf6e9-615e-4c5f-bb12-e994f0ec113d)
![image](https://github.com/noracai26/SimpleParsing/assets/97464986/588d98ed-b7fe-4d9c-b21d-e8e47d6809b0)



### Overall

Old result:

![image](https://github.com/noracai26/SimpleParsing/assets/76873802/8d8e2c1e-9066-43c6-b77f-f3e3a1a953c4)

<Provide a screenshot of the new coverage results by running the existing tool using all test modifications made by the group>
New result:

![5203FD40-78B8-4387-8AA3-2DEED960CAD5_4_5005_c](https://github.com/noracai26/SimpleParsing/assets/90709657/d9827642-a80c-4005-af8a-5082ed2dfaac)

## Statement of individual contributions


<Write what each group member did>
Karina Sudnicina: found the project, implemented coverage tool for two functions mentioned above, created a test cases for them.
