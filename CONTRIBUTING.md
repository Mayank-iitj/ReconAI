# Contributing to SmartRecon-AI

Thank you for your interest in contributing to SmartRecon-AI! We welcome contributions from the community.

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code.

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility and apologize when mistakes happen
- Prioritize what is best for the community

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, Docker version)
- Logs or error messages

### Suggesting Features

Feature requests are welcome! Please provide:
- Clear use case and motivation
- Detailed description of proposed feature
- Potential implementation approach
- Any relevant examples or mockups

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Follow code style guidelines (see below)
   - Add tests for new functionality
   - Update documentation as needed
4. **Run tests**
   ```bash
   pytest
   ```
5. **Commit your changes**
   ```bash
   git commit -m "Add feature: description"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Open a Pull Request**

## Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/smartrecon-ai.git
cd smartrecon-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use Black for formatting
- Use Ruff for linting

```bash
# Format code
black backend/

# Lint code
ruff check backend/

# Type check
mypy backend/
```

### TypeScript/React
- Follow Airbnb style guide
- Use ESLint and Prettier
- Prefer functional components with hooks
- Use TypeScript for all new code

```bash
# Lint frontend
cd frontend
npm run lint

# Format
npm run format
```

## Testing

- Write tests for all new features
- Maintain >80% code coverage
- Use pytest for backend tests
- Use Jest/React Testing Library for frontend tests

```bash
# Run backend tests
pytest backend/tests/

# Run with coverage
pytest --cov=app backend/tests/

# Run frontend tests
cd frontend
npm test
```

## Documentation

- Update README.md for user-facing changes
- Update API.md for API changes
- Add docstrings to all functions and classes
- Include examples in documentation

## Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```
feat(scanner): add FFUF fuzzing support

Implemented FFUF wrapper for directory and parameter fuzzing.
Added configuration options for wordlists and threads.

Closes #123
```

## Tool Wrapper Guidelines

When adding new recon tool wrappers:

1. **Inherit from BaseToolWrapper**
2. **Implement required methods**:
   - `build_command()`: Build CLI command
   - `parse_output()`: Parse and normalize output
3. **Handle errors gracefully**
4. **Add comprehensive tests**
5. **Document in README**

Example:
```python
class NewToolWrapper(BaseToolWrapper):
    def build_command(self, target: str, **kwargs) -> List[str]:
        return ["newtool", "-t", target]
    
    def parse_output(self, output: str) -> List[Dict[str, Any]]:
        # Parse and normalize output
        return results
```

## Security

- Never commit secrets or API keys
- Use environment variables for sensitive data
- Validate all user inputs
- Follow OWASP security guidelines
- Report security vulnerabilities privately to security@smartrecon.ai

## LLM Integration

When adding LLM provider support:

1. Implement `BaseLLMProvider` interface
2. Add provider configuration to settings
3. Handle API errors with retries
4. Add tests with mocked API calls
5. Document API key requirements

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Open a GitHub issue
- Join our Discord: https://discord.gg/smartrecon
- Email: contributors@smartrecon.ai

Thank you for contributing! 🙏
