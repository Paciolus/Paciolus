# CloseSignify Security Rules

## Zero-Storage Policy (MANDATORY)

**All accounting data must remain in-memory only. No exceptions.**

### Rules

1. **No Disk Writes for User Data**
   - All uploaded CSV/Excel files must be processed using `io.BytesIO`
   - Never use `open()` with write mode for accounting data
   - Never use `tempfile` for accounting data
   - Never save DataFrames to disk

2. **Allowed Storage Exceptions**
   - `waitlist.csv` - Email collection only (no accounting data)
   - Application logs (no PII or financial data)
   - Static assets and configuration files

3. **Memory Management**
   - Clear BytesIO buffers after processing
   - Use context managers for all stream operations
   - Implement explicit garbage collection for large datasets

4. **Prohibited Patterns**
   ```python
   # NEVER DO THIS with accounting data:
   df.to_csv("file.csv")
   with open("data.csv", "w") as f:
   tempfile.NamedTemporaryFile()
   shutil.copy(uploaded_file, destination)
   ```

5. **Required Patterns**
   ```python
   # ALWAYS DO THIS:
   buffer = io.BytesIO()
   df = pd.read_csv(io.BytesIO(uploaded_bytes))
   # Process in memory, return results, clear buffer
   buffer.close()
   ```

## Rationale

Fractional CFOs handle sensitive client financial data. Zero-Storage ensures:
- No data remnants on shared infrastructure
- Compliance with client data handling requirements
- Reduced attack surface for data breaches
