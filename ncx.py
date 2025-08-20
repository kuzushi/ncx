#!/usr/bin/env python3
"""
ncx.py — A thin wrapper that proxies to the real `nc` (netcat),
captures its output, and asks OpenAI (via LangChain) to explain it.

Usage:
  nc <normal nc args...>
Environment:
  NC_REAL         Path to the real nc binary (e.g., /usr/bin/nc). REQUIRED for safety.
  OPENAI_API_KEY  Your API key.
  OPENAI_MODEL    Optional. Defaults to "gpt-4o-mini".
"""

import os
import sys
import shlex
import shutil
import subprocess
from typing import Tuple

try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
except ImportError:
    sys.stderr.write(
        "[ncx] Missing dependencies. Install with:\n"
        "  pip install langchain langchain-openai\n"
    )
    sys.exit(2)

EXPLAINER_SYSTEM_PROMPT = """You are a senior network analyst. Given raw netcat (nc) output, provide a concise,
useful explanation for a technical user. Focus on:
- What the output implies (e.g., service banners, protocol hints, open/closed behavior).
- Likely service and version (with uncertainty clearly stated).
- Common next steps to validate (safe/legit methods; no illegal activity).
- If output is empty or ambiguous, explain likely reasons (e.g., -z scans, filtered ports, TLS needed).
Keep it practical and brief unless details are significant.
"""

EXPLAINER_HUMAN_PROMPT = """Raw nc command:
```
{cmd}
```

Exit code: {code}

stdout:
```
{stdout}
```

stderr:
```
{stderr}
```

Please explain what this likely means, including probable service/protocol inferences,
and recommended next steps to validate safely.
"""

def find_real_nc() -> str:
    env_path = os.environ.get("NC_REAL")
    if env_path and os.path.isfile(env_path) and os.access(env_path, os.X_OK):
        return env_path

    candidates = ["/usr/bin/nc", "/bin/nc", "/usr/local/bin/nc", "/sbin/nc"]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c

    which_nc = shutil.which("nc")
    if which_nc:
        return which_nc

    sys.stderr.write(
        "[ncx] Could not locate real netcat. Set NC_REAL to your nc binary, e.g.:\n"
        "  export NC_REAL=/usr/bin/nc\n"
    )
    sys.exit(2)

def run_nc(nc_path: str, argv: list) -> Tuple[int, bytes, bytes]:
    try:
        proc = subprocess.Popen(
            [nc_path] + argv,
            stdin=sys.stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout, stderr
    except FileNotFoundError:
        sys.stderr.write(f"[ncx] nc not found at {nc_path}\n")
        sys.exit(2)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        sys.stderr.write(f"[ncx] Error running nc: {e}\n")
        sys.exit(2)

def explain_with_ai(cmd: str, code: int, stdout: str, stderr: str) -> str:
    model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    llm = ChatOpenAI(
        model=model_name,
        temperature=0.2,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", EXPLAINER_SYSTEM_PROMPT),
        ("human", EXPLAINER_HUMAN_PROMPT),
    ])

    chain = prompt | llm

    resp = chain.invoke({
        "cmd": cmd,
        "code": code,
        "stdout": stdout if stdout.strip() else "(empty)",
        "stderr": stderr if stderr.strip() else "(empty)",
    })

    return resp.content if hasattr(resp, "content") else str(resp)

def main():
    nc_args = sys.argv[1:]
    real_nc = find_real_nc()
    cmd_str = f"{real_nc} " + " ".join(shlex.quote(a) for a in nc_args)
    code, out_b, err_b = run_nc(real_nc, nc_args)
    out_s = out_b.decode(errors="replace")
    err_s = err_b.decode(errors="replace")

    if out_s:
        sys.stdout.write(out_s)
        if not out_s.endswith("\n"):
            sys.stdout.write("\n")
    if err_s:
        sys.stderr.write(err_s)
        if not err_s.endswith("\n"):
            sys.stderr.write("\n")

    print("\n=== AI EXPLANATION (LangChain/OpenAI) ===\n")

    try:
        explanation = explain_with_ai(cmd_str, code, out_s, err_s)
        print(explanation.strip())
    except KeyboardInterrupt:
        raise
    except Exception as e:
        sys.stderr.write(f"[ncx] AI explanation failed: {e}\n")
        sys.exit(code)

    sys.exit(code)

if __name__ == "__main__":
    main()
