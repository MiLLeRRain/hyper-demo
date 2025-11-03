# GitHub Actions Workflows

## Tests Workflow

**File**: `tests.yml`

### Trigger Conditions
- **Pull Requests** to `master` or `main` branch
- **Direct pushes** to `master` or `main` branch

### What It Does

1. **Multi-Python Version Testing**
   - Tests against Python 3.11, 3.12, and 3.13
   - Ensures compatibility across versions

2. **Automated Testing**
   - Installs all dependencies from `requirements.txt`
   - Runs full pytest suite with coverage
   - Requires minimum 80% code coverage
   - Fails if coverage drops below threshold

3. **Code Quality Checks**
   - Runs pylint with project standards
   - Requires score ≥ 8.0 (configured as warning, doesn't block)

4. **Coverage Reporting**
   - Uploads coverage to Codecov (optional, requires token)
   - Generates XML coverage report

### Status Badge

Add this to your `README.md` to show test status:

```markdown
![Tests](https://github.com/MiLLeRRain/hyper-demo/actions/workflows/tests.yml/badge.svg)
```

### Setup Requirements

**Optional - Codecov Integration**:
1. Sign up at https://codecov.io
2. Add your repository
3. Get the upload token
4. Add it as GitHub secret: `Settings` → `Secrets` → `New repository secret`
   - Name: `CODECOV_TOKEN`
   - Value: `<your-token>`

Without Codecov token, the workflow still works - it just skips coverage upload.

### Local Testing

Before pushing, test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest --cov=src/trading_bot --cov-report=term --cov-fail-under=80 -v

# Run pylint
pylint src/trading_bot --rcfile=.pylintrc --fail-under=8.0
```

### Workflow Results

- ✅ **Green check**: All tests passed, coverage ≥ 80%
- ❌ **Red X**: Tests failed or coverage < 80%
- 🟡 **Yellow dot**: Workflow running

### Customization

To modify test requirements, edit `.github/workflows/tests.yml`:

- **Python versions**: Change `matrix.python-version`
- **Coverage threshold**: Change `--cov-fail-under=80`
- **Pylint threshold**: Change `--fail-under=8.0`
- **Test timeout**: Add `timeout-minutes: 10` to test job

### Example PR Flow

1. Developer creates PR
2. GitHub Actions automatically triggers
3. Tests run on 3 Python versions (3.11, 3.12, 3.13)
4. PR shows test status
5. Reviewers can see if tests pass before merging
6. Merge only allowed if tests pass (optional branch protection)

### Enabling Branch Protection

To require tests before merging:

1. Go to repository `Settings`
2. Click `Branches`
3. Add branch protection rule for `master`
4. Check: `Require status checks to pass before merging`
5. Select: `test` workflow
6. Check: `Require branches to be up to date before merging`

Now PRs can only be merged if tests pass!
