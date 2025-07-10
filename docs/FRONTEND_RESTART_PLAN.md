# Frontend Restart Plan - Cognie Calendar App

## 🎯 **Goal**
Create a clean, simple frontend focused on the core calendar feature that auto-generates study plans and helps users stick to them.

## 📊 **Current Issues Analysis**

### Backend Issues
- [ ] `ModuleNotFoundError: No module named 'models.habit'`
- [ ] `ImportError: cannot import name 'OpenAIService'`
- [ ] Performance monitor errors with `to_dict` method
- [ ] Port conflicts (8001 already in use)

### Frontend Issues
- [ ] Material-UI dependency conflicts
- [ ] Missing icon imports (MenuBook, PriorityMedium, etc.)
- [ ] Build cache corruption
- [ ] Multiple Next.js instances running
- [ ] Complex component structure with too many dependencies

## 🏗️ **Architecture Plan**

### 1. **Backend First Approach**
```
Phase 1: Fix Backend
├── Resolve import issues
├── Fix service dependencies
├── Simplify performance monitoring
└── Ensure clean startup

Phase 2: Simple Frontend
├── Minimal dependencies
├── Focus on calendar core
├── Clean component structure
└── Progressive enhancement
```

### 2. **Technology Stack Simplification**
```
Current (Complex):
├── Material-UI (with icon conflicts)
├── Multiple date pickers
├── Complex state management
└── Many external dependencies

Proposed (Simple):
├── Vanilla CSS + Tailwind (if needed)
├── Simple date handling
├── React hooks for state
└── Minimal external deps
```

## 📝 **Implementation Plan**

### **Step 1: Backend Cleanup**
1. **Fix Import Issues**
   - Check `models/habit.py` exists and is properly structured
   - Fix `routes/habits.py` import
   - Resolve `OpenAIService` vs `EnhancedOpenAIService` naming

2. **Service Dependencies**
   - Audit all service imports
   - Ensure consistent naming
   - Fix performance monitor issues

3. **Port Management**
   - Kill all existing processes
   - Use consistent ports (8001 for backend, 3000 for frontend)

### **Step 2: Frontend Restart**
1. **Clean Slate**
   - Remove all existing frontend files
   - Start with minimal Next.js setup
   - No Material-UI initially

2. **Core Calendar Feature**
   - Simple calendar view
   - Study plan creation form
   - Basic event management
   - Clean, modern UI with CSS

3. **Progressive Enhancement**
   - Add features one by one
   - Test each addition thoroughly
   - Maintain simplicity

### **Step 3: Integration**
1. **API Integration**
   - Simple fetch calls
   - Error handling
   - Loading states

2. **User Experience**
   - Intuitive navigation
   - Clear feedback
   - Responsive design

## 🎨 **UI/UX Design Principles**

### **Simplicity First**
- Clean, minimal interface
- Focus on core functionality
- Intuitive user flows

### **Calendar-Centric**
- Calendar as the main interface
- Easy study plan creation
- Visual progress tracking

### **Mobile-First**
- Responsive design
- Touch-friendly interactions
- Fast loading times

## 🔧 **Technical Specifications**

### **Frontend Stack**
```
Framework: Next.js 14
Styling: CSS Modules or Tailwind CSS
State: React hooks
HTTP: Fetch API or Axios
Icons: Simple SVG icons or heroicons
```

### **Backend Integration**
```
API: RESTful endpoints
Authentication: Simple JWT
Data: JSON responses
Error Handling: Consistent error format
```

## 📋 **Feature Priority List**

### **MVP (Must Have)**
1. ✅ Calendar view
2. ✅ Study plan creation
3. ✅ Basic event management
4. ✅ Simple navigation

### **Phase 2 (Should Have)**
1. 📅 Study session tracking
2. 📊 Progress visualization
3. 🔔 Basic notifications
4. 📱 Mobile optimization

### **Phase 3 (Could Have)**
1. 🤖 AI study recommendations
2. 📈 Advanced analytics
3. 🔗 Integration with other tools
4. 🎨 Advanced UI features

## 🚀 **Success Criteria**

### **Technical**
- [ ] Backend starts without errors
- [ ] Frontend builds successfully
- [ ] No dependency conflicts
- [ ] Clean, maintainable code

### **Functional**
- [ ] Calendar displays correctly
- [ ] Study plans can be created
- [ ] Events can be managed
- [ ] API integration works

### **User Experience**
- [ ] Intuitive interface
- [ ] Fast loading times
- [ ] Responsive design
- [ ] Clear feedback

## ⚠️ **Risk Mitigation**

### **Technical Risks**
- **Dependency Conflicts**: Start with minimal dependencies
- **Build Issues**: Use simple, proven technologies
- **Performance**: Optimize for speed from the start

### **Scope Risks**
- **Feature Creep**: Stick to MVP features
- **Complexity**: Keep it simple
- **Timeline**: Focus on core functionality first

## 📅 **Timeline**

### **Day 1: Backend Fixes**
- Fix all import issues
- Ensure clean startup
- Test API endpoints

### **Day 2: Frontend Foundation**
- Create minimal Next.js app
- Implement basic calendar
- Simple styling

### **Day 3: Core Features**
- Study plan creation
- Event management
- API integration

### **Day 4: Polish & Test**
- UI improvements
- Error handling
- Testing & bug fixes

## 🎯 **Next Steps**

1. **Review this plan**
2. **Confirm approach**
3. **Start with backend fixes**
4. **Build frontend incrementally**
5. **Test thoroughly at each step**

---

**Remember**: Keep it simple, focus on the core calendar feature, and build incrementally. 