# GitHub Copilot Instructions

This file provides context and guidelines for GitHub Copilot when working with this repository.

## Project Overview

SISOC (Sistema de Información Social) is a Django-based management system for social services, deployed using Docker and MySQL. The application manages multiple functional modules including dining halls (comedores), surveys (relevamientos), users, and various social programs.

## Technology Stack

- **Backend**: Django (Python 3.11+)
- **Database**: MySQL
- **Containerization**: Docker + Docker Compose
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Testing**: pytest with pytest-xdist for parallel execution

## Development Setup

### Initial Setup
```bash
# Clone the repository
git clone https://github.com/dsocial118/BACKOFFICE.git
cd BACKOFFICE

# Copy environment configuration
cp .env.example .env
# Edit .env file with your configuration

# Start services with Docker Compose
docker-compose up
```

The application will be available at http://localhost:8000

### Database Setup
- Optionally place a MySQL dump at `./docker/mysql/local-dump.sql` before starting services
- To reset database:
  ```bash
  docker-compose down
  docker volume rm sisoc_mysql_data
  # Place new dump if needed
  docker-compose up
  ```

## Project Structure

- **`config/`** - Django global configuration and settings
- **`docker/`** - Docker container configuration files
- **Application modules** - Each directory represents a functional module:
  - `comedores/` - Dining halls management
  - `relevamientos/` - Surveys and assessments
  - `users/` - User management and authentication
  - `admisiones/` - Admissions
  - `acompanamientos/` - Accompaniments
  - `celiaquia/` - Celiac disease management
  - `centrodefamilia/` - Family center
  - `cdi/` - Child development
  - `intervenciones/` - Interventions
  - And others...
- **`templates/`** - Global HTML templates
  - `templates/components/` - Reusable HTML components
  - Each app also has its own `templates/` subdirectory
- **`static/`** - Static files (CSS, JS, images)
- **`tests/`** - Automated tests
- **`core/`** - Core utilities and shared functionality

## Code Style and Conventions

### Naming Conventions
- **Python**: `snake_case` for variables, functions, methods
- **JavaScript**: `camelCase` for variables and functions
- **CSS**: `kebab-case` for class names

### Django Architecture Guidelines
- **Models**: 
  - Include descriptive docstrings
  - Use `verbose_name` to avoid redundancy
  - Keep models focused on data representation
- **Views**: 
  - Prefer Class-Based Views (CBVs)
  - Keep views thin - no business logic in views
  - Business logic belongs in `services/` modules
- **Templates**: 
  - Avoid database queries in templates
  - Keep templates simple and focused on presentation
  - Use template components from `templates/components/`
- **Services**: 
  - Organize services by model in `services/` directory
  - Put all business logic in service modules

### Code Quality Tools

Run these commands before creating a Pull Request:

```bash
# Python linting (manual fixes required)
pylint **/*.py --rcfile=.pylintrc

# Python formatting (automatic)
black .

# Django template formatting (semi-automatic)
djlint . --configuration=.djlintrc --reformat
```

## Testing

### Running Tests
```bash
# Run all tests in parallel
docker compose exec django pytest -n auto

# Run specific test file
docker compose exec django pytest path/to/test_file.py

# Run with verbose output
docker compose exec django pytest -v
```

### Writing Tests
- Write tests for all business logic changes
- Place tests in `tests/` directory or app-specific test files
- Maintain test coverage for critical functionality
- Follow existing test patterns in the repository

## Git Workflow and Commit Conventions

### Branching Strategy
- Base branch: `development`
- Create feature branches from `development`
- Merge back to `development` via Pull Request

### Commit Message Format
Use conventional commit format:
```
feat: add new functionality to comedores module
fix: correct bug in relevamientos validation
refactor: clean up services in users module
docs: update API documentation
test: add tests for new feature
```

### Pull Request Process
1. Create branch from `development`
2. Make changes and commit using conventional format
3. Run linters and tests
4. Create Pull Request to `development`
5. Ensure at least one code review before merging

## API Documentation

- **Postman Documentation**: [API SISOC Documentation](https://documenter.getpostman.com/view/14921866/2sAXxMfDXf)
- For detailed API specifications, authentication methods, and endpoint documentation, refer to the Postman collection
- For questions or clarifications, contact the tech lead or project owner
- **Authentication**: See `.env.example` for API configuration and authentication setup

Example API request (authentication method varies by endpoint - see Postman docs):
```bash
curl -X GET http://localhost:8000/api/comedores/ \
  -H "Authorization: Bearer <API_KEY>"
```

## Important Guidelines for Code Changes

1. **Never invent**: Don't create APIs, models, endpoints, settings, or dependencies without explicit requirements. If information is missing, leave explicit TODO comments or document assumptions clearly.

2. **Preserve default behavior**: If changing logic or contracts, list breaking changes and update all callers.

3. **Minimal changes first**: Prefer incremental patches. For large refactors, propose first unless absolutely necessary.

4. **Code must compile and pass tests**: Ensure lint + type checking + tests pass, or explicitly document what's pending.

5. **Security by default**: 
   - Validate all inputs
   - Implement proper authorization/authentication
   - Never expose sensitive data
   - Prevent injection attacks (SQL, OS, HTML)

6. **Performance awareness**:
   - Avoid N+1 queries
   - Don't run I/O operations in loops
   - Paginate large lists
   - Don't load entire datasets unnecessarily

7. **Observability**:
   - Useful logs (without PII)
   - Consistent error handling
   - Actionable error messages
   - Add metrics where applicable

8. **Useful comments, not redundant**: Create documentation or add docstrings based on complexity.

9. **Repository consistency**: Follow existing conventions (naming, structure, style). Don't introduce new patterns without reason.

10. **Readable over clever**: Explicit code, clear names, small functions, comments only where they add value.

11. **Handle edge cases**: Consider null/None, empty values, permissions, concurrency, timezones, locales, and backward compatibility.

12. **Tests when logic changes**: Minimum 1 test per critical case. For pure refactors, ensure behavioral parity.

## Deployment

### Release Cycle (Bi-weekly)
- **Week 0 (Thursday)**: Open `development` branch
- **Week 2 (Monday, freeze)**: Freeze `development`, create tag `YY.MM.DD-rc1`
- **Week 2 (Wednesday night)**: Deploy to production if QA approves latest `rcX`

### Deployment Checklist
- [ ] `development` branch frozen (no new features)
- [ ] Valid database backup
- [ ] Final tag created on `development`
- [ ] Tested with production-like database
- [ ] Tag tested in QA environment
- [ ] QA approval obtained
- [ ] Clean merge to `main`
- [ ] CHANGELOG.md updated
- [ ] Migrations are reversible/controlled
- [ ] Team notified
- [ ] Last stable tag saved for rollback
- [ ] Stable migrations squashed

## Additional Resources

- **README.md**: Comprehensive project documentation
- **CHANGELOG.md**: Version history and changes
- **AGENTS.md**: AI assistant recommendations (Spanish)
- **.codex/rules.md**: Detailed coding rules and guidelines
- **docs/indice.md**: Documentation index

## Environment Variables

See `.env.example` for required environment variables. Key variables are documented in the README.md file.

## VSCode Debugging

1. Start services: `docker-compose up`
2. Select `Django in Docker` configuration in VS Code debug panel
3. Set breakpoints and start debugging

## Contact and Support

For technical questions or clarifications, refer to the project documentation or contact the technical lead.