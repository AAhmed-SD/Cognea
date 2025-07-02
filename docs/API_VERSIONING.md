# API Versioning Strategy

## Overview

This document outlines the API versioning strategy for Cognie, ensuring backward compatibility and smooth transitions for API consumers.

## Versioning Approach

### URL Path Versioning

We use URL path versioning for clear, explicit versioning:

```
/api/v1/tasks/
/api/v1/goals/
/api/v2/tasks/
/api/v2/goals/
```

### Benefits
- **Explicit**: Clear version in URL
- **Simple**: Easy to understand and implement
- **Flexible**: Can run multiple versions simultaneously
- **Cacheable**: Each version can be cached independently

## Version Lifecycle

### Version States

1. **Current** (v1): Latest stable version
2. **Beta** (v2): New features in testing
3. **Deprecated** (v0): Old version with deprecation warnings
4. **Retired** (v0): No longer supported

### Version Timeline

```
v1 (Current) ←→ v2 (Beta) ←→ v3 (Future)
     ↓              ↓
  Deprecated    Current
     ↓              ↓
   Retired     Deprecated
```

## Version Management

### Version Naming Convention

- **Major Version**: Breaking changes (v1, v2, v3)
- **Minor Version**: New features, backward compatible (v1.1, v1.2)
- **Patch Version**: Bug fixes (v1.1.1, v1.1.2)

### Version Deprecation Policy

1. **Announcement**: 6 months before deprecation
2. **Deprecation**: 3 months with warnings
3. **Retirement**: Complete removal after 3 months

## Implementation

### FastAPI Route Structure

```python
# routes/v1/tasks.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

@router.get("/tasks/")
async def get_tasks():
    # v1 implementation
    pass

# routes/v2/tasks.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v2")

@router.get("/tasks/")
async def get_tasks():
    # v2 implementation with new features
    pass
```

### Main Application

```python
# main.py
from fastapi import FastAPI
from routes import v1, v2

app = FastAPI()

# Include versioned routers
app.include_router(v1.router, prefix="/api/v1")
app.include_router(v2.router, prefix="/api/v2")

# Default version redirect
@app.get("/api/tasks/")
async def redirect_to_current_version():
    return RedirectResponse(url="/api/v1/tasks/")
```

## Breaking Changes

### What Constitutes Breaking Changes

1. **Removing endpoints**
2. **Changing response structure**
3. **Modifying required parameters**
4. **Changing authentication methods**
5. **Altering error codes**

### Breaking Change Process

1. **Design Phase**
   - Plan new API structure
   - Document changes
   - Create migration guide

2. **Development Phase**
   - Implement new version
   - Maintain old version
   - Add deprecation warnings

3. **Testing Phase**
   - Test both versions
   - Validate migration paths
   - Performance testing

4. **Release Phase**
   - Deploy new version
   - Update documentation
   - Notify users

## Migration Guidelines

### For API Consumers

#### Gradual Migration
```javascript
// Old code (v1)
const response = await fetch('/api/v1/tasks/');

// New code (v2)
const response = await fetch('/api/v2/tasks/');
```

#### Feature Detection
```javascript
// Check API version support
const checkVersion = async () => {
  try {
    const response = await fetch('/api/v2/tasks/');
    return response.ok;
  } catch {
    return false;
  }
};
```

### Migration Checklist

- [ ] Update API endpoints to new version
- [ ] Handle new response formats
- [ ] Update error handling
- [ ] Test all functionality
- [ ] Update documentation
- [ ] Monitor for issues

## Version-Specific Features

### v1 Features (Current)

```python
# Basic CRUD operations
GET    /api/v1/tasks/
POST   /api/v1/tasks/
GET    /api/v1/tasks/{id}
PUT    /api/v1/tasks/{id}
DELETE /api/v1/tasks/{id}

# Basic filtering
GET /api/v1/tasks/?status=pending&priority=high
```

### v2 Features (Beta)

```python
# Enhanced CRUD with bulk operations
GET    /api/v2/tasks/
POST   /api/v2/tasks/
POST   /api/v2/tasks/bulk
GET    /api/v2/tasks/{id}
PUT    /api/v2/tasks/{id}
DELETE /api/v2/tasks/{id}

# Advanced filtering and search
GET /api/v2/tasks/?search=project&status=pending&priority=high&due_date=2024-01-15

# AI-powered features
POST /api/v2/tasks/generate
POST /api/v2/tasks/optimize
```

## Documentation Strategy

### Version-Specific Docs

```
docs/
├── api/
│   ├── v1/
│   │   ├── endpoints.md
│   │   ├── examples.md
│   │   └── migration.md
│   └── v2/
│       ├── endpoints.md
│       ├── examples.md
│       └── migration.md
```

### API Documentation URLs

- **v1 Docs**: `/docs/api/v1`
- **v2 Docs**: `/docs/api/v2`
- **Migration Guide**: `/docs/api/migration`
- **Changelog**: `/docs/api/changelog`

## Testing Strategy

### Version Testing

```python
# tests/test_api_versions.py
import pytest
from fastapi.testclient import TestClient

def test_v1_endpoints():
    client = TestClient(app)
    response = client.get("/api/v1/tasks/")
    assert response.status_code == 200

def test_v2_endpoints():
    client = TestClient(app)
    response = client.get("/api/v2/tasks/")
    assert response.status_code == 200

def test_version_compatibility():
    # Test that v1 and v2 return compatible data
    pass
```

### Backward Compatibility Tests

```python
def test_backward_compatibility():
    # Ensure v2 can handle v1-style requests
    client = TestClient(app)
    
    # v1 request to v2 endpoint
    response = client.get("/api/v2/tasks/?status=pending")
    assert response.status_code == 200
    
    # Verify response structure is compatible
    data = response.json()
    assert "tasks" in data
```

## Monitoring and Analytics

### Version Usage Tracking

```python
# middleware/version_tracking.py
from fastapi import Request
import logging

async def track_api_version(request: Request, call_next):
    version = request.url.path.split('/')[2]  # Extract version from path
    logging.info(f"API Version Used: {version}")
    
    response = await call_next(request)
    return response
```

### Metrics to Track

- **Version adoption rate**
- **Error rates by version**
- **Performance metrics by version**
- **Migration progress**

## Security Considerations

### Version-Specific Security

```python
# Different security policies per version
def get_security_policy(version: str):
    if version == "v1":
        return BasicAuth()
    elif version == "v2":
        return JWTAuth()
    else:
        return DefaultAuth()
```

### Deprecation Security

- **Rate limiting**: Stricter limits on deprecated versions
- **Access control**: Gradual restriction of deprecated endpoints
- **Monitoring**: Enhanced monitoring for deprecated versions

## Future Planning

### v3 Roadmap

1. **GraphQL Support**: Add GraphQL alongside REST
2. **Real-time Features**: WebSocket support
3. **Advanced AI**: Enhanced AI-powered features
4. **Microservices**: Service decomposition

### Long-term Strategy

- **API Gateway**: Centralized API management
- **Service Mesh**: Inter-service communication
- **Event-driven**: Event sourcing and CQRS
- **Multi-tenancy**: Advanced tenant isolation

## Best Practices

### For Developers

1. **Always maintain backward compatibility**
2. **Document all changes thoroughly**
3. **Test both versions during transitions**
4. **Monitor version usage and performance**
5. **Plan migrations well in advance**

### For API Consumers

1. **Use feature detection for new versions**
2. **Implement graceful fallbacks**
3. **Monitor deprecation warnings**
4. **Plan migration timelines**
5. **Test thoroughly before switching**

## Conclusion

This versioning strategy ensures:

- **Stability**: Existing integrations continue to work
- **Innovation**: New features can be added safely
- **Clarity**: Clear communication about changes
- **Flexibility**: Multiple versions can coexist
- **Security**: Proper security controls per version

By following this strategy, we maintain a balance between innovation and stability, ensuring a smooth experience for all API consumers. 