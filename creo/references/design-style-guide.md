# Design Review Style Guide

## Configuration

Customize this file for your project. Check `.claude/project-config.md` for overrides.

## Default Dev Server

- **URL:** `http://localhost:3000`
- Change to match your project's dev server port (configure in `.claude/project-config.md`)

## Testing Viewports

### Standard Breakpoints

- **375px** - Mobile baseline (iPhone SE, small phones)
- **768px** - Tablet baseline (iPad portrait)
- **1440px** - Desktop baseline (standard laptop)
- **1920px** - Large desktop baseline (full HD)

### Mobile-First Implementation Rules

1. Start with mobile (375px) styling
2. Use responsive props/classes progressively
3. Test touch targets: minimum 44px for interactive elements
4. Ensure content is readable at all breakpoint sizes

## Component Standards

### Spacing System

- **Base Unit:** 8px (or 4px for finer control)
- **Common values:** 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px

### Typography Scale

- **H1:** 32-48px (responsive)
- **H2:** 24-36px (responsive)
- **H3:** 20-28px (responsive)
- **H4:** 18-24px (responsive)
- **Body:** 14-16px
- **Small:** 12-14px
- **Caption:** 10-12px

### Color Contrast Requirements (WCAG AA)

- **Normal text:** 4.5:1 minimum contrast ratio
- **Large text (18px+):** 3:1 minimum contrast ratio
- **Interactive elements:** Clear visual distinction

### Touch Target Sizes

- **Minimum:** 44x44px for all interactive elements
- **Recommended:** 48x48px for primary actions
- **Spacing:** At least 8px between adjacent targets

## Accessibility Checklist

### Focus States

- [ ] All interactive elements have visible focus indicators
- [ ] Focus order follows logical reading order
- [ ] Skip links available for keyboard users

### Screen Reader Support

- [ ] All images have alt text
- [ ] Form inputs have associated labels
- [ ] ARIA roles used appropriately
- [ ] Headings follow proper hierarchy (H1, H2, H3)

### Motion & Animation

- [ ] Respect `prefers-reduced-motion`
- [ ] Animations are subtle and quick (150-300ms)
- [ ] No flashing content (3 flashes/second max)

## Framework-Specific Notes

### If using Tailwind CSS

```
Breakpoints: sm:640px, md:768px, lg:1024px, xl:1280px, 2xl:1536px
```

### If using MUI (Material-UI)

```
Breakpoints: xs:0px, sm:600px, md:900px, lg:1200px, xl:1536px
Use sx props with breakpoint objects: sx={{ width: { xs: '100%', md: '50%' } }}
```

### If using shadcn/ui

```
Based on Tailwind breakpoints
Use responsive utilities: className="w-full md:w-1/2"
```

---

**Note:** Update this file to match your project's design system and framework.
