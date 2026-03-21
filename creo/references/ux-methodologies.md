# Professional UX Methodologies Reference

## 1. Nielsen's 10 Usability Heuristics

Reference: [Nielsen Norman Group](https://www.nngroup.com/articles/ten-usability-heuristics/)

### H1: Visibility of System Status
The design should always keep users informed about what is going on. Progress indicators, loading spinners, success/error toasts, "Saving..." indicators. Ask: Does the user know what is happening? Is the current state visible?

### H2: Match Between System and Real World
The design should speak the users' language. Use familiar terms ("Shopping Cart" not "Item Repository"), calendar for dates, familiar icons. Ask: Would a new user understand this term?

### H3: User Control and Freedom
Users need a clearly marked "emergency exit." Undo/redo, cancel buttons, easy navigation back, "Save as Draft." Ask: Can users easily back out? Can they undo mistakes?

### H4: Consistency and Standards
Users should not wonder whether different words, situations, or actions mean the same thing. Same button styles, consistent terminology, predictable behavior. Ask: Is this pattern used elsewhere in the app?

### H5: Error Prevention
Good designs prevent problems from occurring. Disable submit until valid, confirmation dialogs for destructive actions, input constraints. Ask: What mistakes could users make? How can we prevent them?

### H6: Recognition Rather Than Recall
Minimize memory load by making elements visible. Dropdowns with recent items, visible navigation, contextual help, search suggestions. Ask: Does the user need to remember something? Can we show it instead?

### H7: Flexibility and Efficiency of Use
Accelerators unseen by novices may speed up expert interaction. Keyboard shortcuts, recent items, bulk actions, templates. Ask: How do experts complete this task?

### H8: Aesthetic and Minimalist Design
Interfaces should not contain irrelevant or rarely needed information. Clean interfaces, progressive disclosure, show only what is needed. Ask: What can we remove?

### H9: Help Users Recognize, Diagnose, and Recover from Errors
Error messages should be in plain language. "Email address is invalid" not "Error 422." Highlight the field, suggest fixes, preserve input. Ask: Is the error message helpful?

### H10: Help and Documentation
It is best if the system needs no documentation, but it may be necessary. Inline help, tooltips, contextual help links, onboarding tutorials. Ask: Where might users get stuck?

---

## 2. Jobs-to-be-Done (JTBD) Framework

### JTBD Statement Formula

```
When [SITUATION/CONTEXT],
I want to [MOTIVATION/ACTION],
So I can [EXPECTED OUTCOME/BENEFIT].
```

### Job Types

| Type | Description | Example |
|------|-------------|---------|
| **Functional** | The practical task | "Send an invoice" |
| **Emotional** | The feeling sought | "Feel professional" |
| **Social** | How perceived by others | "Appear organized" |
| **Supporting** | Related secondary tasks | "Track payment status" |

---

## 3. User Journey Mapping

### Journey Map Components

| Component | Description |
|-----------|-------------|
| **Stages** | Major phases of the journey |
| **Actions** | What user does at each stage |
| **Touchpoints** | Where interaction happens |
| **Thoughts** | What user is thinking |
| **Emotions** | How user feels |
| **Pain Points** | Friction and frustration |
| **Opportunities** | Where to improve |

### Pain Point Categories

1. **Process Pain**: Too many steps, confusing flow
2. **Information Pain**: Missing info, unclear instructions
3. **Interaction Pain**: Hard to click, slow response
4. **Emotional Pain**: Frustrating, anxiety-inducing

---

## 4. Complexity Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Step Count** | Total user actions | < 5 for common tasks |
| **Decision Points** | Choices user must make | Minimize |
| **Form Fields** | Inputs required | < 7 visible at once |
| **Time to Complete** | End-to-end duration | < 2 min for simple tasks |
| **Error Rate** | Failures / attempts | < 5% |

---

## 5. Simplification Patterns

1. **Progressive Disclosure** -- Show basic options first, advanced on demand.
2. **Smart Defaults** -- Pre-select the most common option (e.g., detect language from browser).
3. **Inline Editing** -- Edit in place instead of separate screen.
4. **Wizard Optimization** -- Reduce steps, allow skipping, show progress.
5. **Contextual Actions** -- Show actions where relevant (hover to reveal edit/delete).

---

## 6. Severity Rating Scale

| Severity | Description | Priority | Action |
|----------|-------------|----------|--------|
| **0** | Not a usability problem | Skip | No action needed |
| **1** | Cosmetic only | Low | Fix if time permits |
| **2** | Minor problem | Medium | Low priority fix |
| **3** | Major problem | High | Important to fix |
| **4** | Usability catastrophe | Critical | Must fix before launch |

### Severity Decision Tree

```
Does user's task fail completely?
  YES -> Severity 4
  NO  -> Does user struggle significantly?
           YES -> Severity 3
           NO  -> Does user notice issue?
                    YES -> Severity 2
                    NO  -> Is there any issue?
                             YES -> Severity 1
                             NO  -> Severity 0
```

---

## Sources

- [Nielsen Norman Group - 10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)
- [JTBD Framework Guide](https://www.userinterviews.com/ux-research-field-guide-chapter/jobs-to-be-done-jtbd-framework)
- [User Journey Mapping](https://www.flowmapp.com/features/userflow)
