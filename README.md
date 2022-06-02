# Stylezilla

A VS Code extension to detect and flag micro-antipatterns in students' Python code.

For example:

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/Uz4FmPskNEY" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

## Development

Stylezilla is still in the development stage.
To get started with development, make sure you have Python 3.10 installed before doing the following:

1. Create a venv: `python3 -m venv venv`, and activate it: `source venv/bin/activate`
2. Install Python requirements: `pip install -r requirements.txt`
3. Install npm requirements: `npm install && cd client && npm install`

To run the extension go to the `Run and Debug` menu and select `Server + Client` from the configuration dropdown (top left). Then, run the debugger.