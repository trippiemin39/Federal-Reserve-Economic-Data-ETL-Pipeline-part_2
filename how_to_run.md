## How to run

**1. Clone the repository**

```bash
git clone https://github.com/trippiemin39/Federal-Reserve-Economic-Data-ETL-Pipeline-part_2.git
cd Federal-Reserve-Economic-Data-ETL-Pipeline-part_2
```

**2. Install the dependencies**

```bash
pip install -r requirements.txt
```

**3. Get two free API keys**

- FRED: [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
- EIA: [eia.gov/opendata](https://www.eia.gov/opendata/)

**4. Add your API keys**

Create a folder `API_CODE` with two text files. Put only the key in each file.

```
API_CODE/
├── FRED_API.txt   <-- your FRED key
└── EIA_API.txt    <-- your EIA key
```

This folder is in `.gitignore`, so your keys are never uploaded.

**5. Run the pipeline**

```bash
python ETL.py
```

This creates `FREDDY.db` with the full star schema.
