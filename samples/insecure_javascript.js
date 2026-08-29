const apiKey = "api-secret-key-123456";
function render(input) {
  document.querySelector('#output').innerHTML = input;
  console.log(apiKey);
  return eval(input);
}
