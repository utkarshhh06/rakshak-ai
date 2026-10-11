# Rakshak AI MVP (synthetic-data demo)

## Run on Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If `.venv` already exists, reuse it. If PowerShell activation is unavailable, you can run `python -m pip install -r requirements.txt` and `python -m streamlit run app.py` using the intended Python environment.

## Tests

```powershell
python -m pytest -q
```

## Safety

This is a transparent heuristic demo using fictional scenarios. It is not a calibrated fraud probability, does not establish that a transaction is fraudulent or safe, and does not connect to or take actions on real payment systems. Do not enter real customer data, account numbers, or UPI IDs.
