const evaluate = require('static-eval');
const parse = require('esprima').parse;

var src = process.argv[2];

var ast = parse(src).body[0].expression;

var result = evaluate(ast);
console.log("result: ", result);
