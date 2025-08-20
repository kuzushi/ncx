# ncx
ai empowered net cat


# ncx Wrapper Setup

This wrapper lets you use `nc` (netcat) as usual, but after execution it will call OpenAI (via LangChain) to provide an explanation of the results.

## Installation

1. Clone or copy the `ncx.py` file to your system:

   ```bash
   cp ncx.py ~/bin/ncx.py
   chmod +x ~/bin/ncx.py
   ```

2. Install dependencies:

   ```bash
   pip install langchain langchain-openai
   ```

3. Set your environment variables:

   ```bash
   export OPENAI_API_KEY="sk-..."
   export OPENAI_MODEL="gpt-4o-mini"   # optional, defaults to gpt-4o-mini
   export NC_REAL="/usr/bin/nc"        # adjust to your system's nc path
   ```

4. Alias `nc` to the wrapper:

   ```bash
   alias nc='python3 ~/bin/ncx.py'
   ```

## Usage

Run `nc` commands as usual:

```bash
nc -v example.com 80
```

The wrapper will:
- Run the real `nc` and display its raw output.
- Then print an **AI Explanation** interpreting what the results mean.

## Notes

- To run the original netcat directly, use the absolute path: `/usr/bin/nc`.
- The wrapper captures output only after `nc` finishes (not streaming in real time).
- Works best for banner grabbing and quick probes; interactive sessions may not be ideal.

