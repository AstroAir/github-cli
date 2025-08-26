# Responsive CSS for Authentication Components

This document describes the responsive CSS styling system implemented for GitHub CLI authentication components.

## Overview

The responsive CSS system provides adaptive styling for authentication screens across different terminal sizes, ensuring optimal user experience regardless of screen dimensions. The system includes breakpoint-specific rules, adaptive spacing, responsive button layouts, text truncation handling, and comprehensive accessibility support.

## File Structure

- `responsive_auth.tcss` - Main responsive CSS file for authentication components
- `accessibility.tcss` - Accessibility-specific styles (existing)
- `visual_feedback.tcss` - Visual feedback styles (existing)

## Breakpoint System

The responsive system uses three main breakpoints:

### Compact Layout (< 60 columns, < 15 rows)

- **Target**: Small terminals, mobile-like environments
- **Features**:
  - Minimal padding and margins
  - Vertical button layouts
  - Text truncation enabled
  - Non-essential elements hidden
  - Simplified visual hierarchy

### Standard Layout (60-100 columns, 15-25 rows)

- **Target**: Medium terminals, typical desktop usage
- **Features**:
  - Balanced spacing
  - Horizontal button layouts
  - Full instruction text
  - Standard visual elements
  - Moderate information density

### Expanded Layout (> 100 columns, > 25 rows)

- **Target**: Large terminals, wide screens
- **Features**:
  - Comfortable spacing
  - Rich visual elements
  - Detailed progress information
  - Enhanced animations
  - Maximum information density

## CSS Class Structure

### Base Classes

```css
.auth-screen                 /* Base authentication screen */
.auth-screen-container       /* Main container */
.auth-header                 /* Header section */
.auth-title                  /* Screen title */
.auth-subtitle               /* Screen subtitle */
```

### Component Classes

```css
.device-code-container       /* Device code display */
.device-code                 /* Device code text */
.verification-url-container  /* URL display container */
.verification-url            /* URL text */
.auth-instructions           /* Instruction text */
.auth-buttons                /* Button container */
.auth-button                 /* Individual buttons */
.auth-progress               /* Progress indicators */
.auth-status                 /* Status messages */
```

### Responsive Modifiers

```css
.auth-screen.compact         /* Compact layout styles */
.auth-screen.standard        /* Standard layout styles */
.auth-screen.expanded        /* Expanded layout styles */
```

### Utility Classes

```css
.text-truncate              /* Text truncation */
.text-wrap                  /* Text wrapping */
.spacing-compact            /* Minimal spacing */
.spacing-normal             /* Normal spacing */
.spacing-comfortable        /* Comfortable spacing */
.hidden                     /* Hide elements */
.visible                    /* Show elements */
.center                     /* Center alignment */
```

## Responsive Features

### Adaptive Spacing

The system automatically adjusts padding and margins based on screen size:

- **Compact**: Minimal spacing (0-1 units)
- **Standard**: Normal spacing (1-2 units)
- **Expanded**: Comfortable spacing (2-3 units)

### Button Layout Adaptation

Button layouts change based on available space:

- **Compact**: Vertical stacking, full-width buttons
- **Standard**: Horizontal layout with adequate spacing
- **Expanded**: Horizontal layout with generous spacing

### Text Handling

Text content adapts to screen constraints:

- **Truncation**: Automatic ellipsis for long text in compact mode
- **Wrapping**: Intelligent word wrapping in standard/expanded modes
- **Overflow**: Hidden overflow with scroll where appropriate

### Visual Hierarchy

Information density adjusts to screen size:

- **Compact**: Essential information only
- **Standard**: Balanced information display
- **Expanded**: Full detail with enhanced visuals

## Accessibility Features

### High Contrast Mode

```css
.auth-screen.high-contrast {
    background: black;
    color: white;
    border: 2px solid white;
}
```

### Enhanced Focus Indicators

```css
.focus-enhanced:focus {
    border: 3px solid $accent;
    outline: 2px solid $primary;
    outline-offset: 2px;
}
```

### Screen Reader Support

```css
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
}
```

### Reduced Motion Support

```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

## Media Queries

The system includes comprehensive media query support:

### System Preferences

```css
@media (prefers-contrast: high)      /* High contrast mode */
@media (prefers-reduced-motion: reduce) /* Reduced motion */
@media (prefers-color-scheme: dark)  /* Dark mode */
```

### Print Styles

```css
@media print {
    /* Optimized for printing/documentation */
}
```

## Usage Examples

### Basic Authentication Screen

```python
# Python component
with Container(classes="auth-screen standard"):
    yield Static("GitHub CLI Authentication", classes="auth-title")
    yield Container(classes="device-code-container"):
        yield Static("ABCD-1234", classes="device-code")
```

### Responsive Button Layout

```python
# Buttons adapt automatically based on screen size
with Container(classes="auth-buttons"):
    yield Button("Continue", classes="auth-button primary")
    yield Button("Cancel", classes="auth-button cancel")
```

### Accessibility-Enhanced Elements

```python
# High contrast and focus support
with Container(classes="auth-screen high-contrast"):
    yield Button("Login", classes="auth-button focus-enhanced")
```

## Integration with Components

### ResponsiveLayoutManager

The CSS system integrates with the `ResponsiveLayoutManager` to automatically apply appropriate classes:

```python
config = layout_manager.get_layout_config()
# config.layout_type determines CSS classes applied
```

### AuthView Components

Each view component automatically receives appropriate CSS classes:

- `CompactAuthView` → `.auth-screen.compact`
- `StandardAuthView` → `.auth-screen.standard`
- `ExpandedAuthView` → `.auth-screen.expanded`

## Testing and Validation

### CSS Validation

Run the CSS validation script:

```bash
python validate_css.py
```

### Integration Testing

Test CSS integration with components:

```bash
python test_css_integration.py
```

### Manual Testing

Test responsive behavior by resizing terminal:

1. Start authentication flow
2. Resize terminal to different sizes
3. Verify layout adapts appropriately
4. Test accessibility features

## Performance Considerations

### Optimizations

- Minimal CSS specificity for fast rendering
- Efficient selector structure
- Reduced animation complexity in compact mode
- Optimized media queries

### Memory Usage

- Lightweight utility classes
- Shared base styles
- Minimal redundancy

## Browser/Terminal Compatibility

### Textual CSS Support

The CSS is designed for Textual's CSS implementation:

- Uses Textual-specific properties
- Compatible with terminal color schemes
- Supports Textual layout system

### Terminal Limitations

- No complex animations in some terminals
- Limited color support in basic terminals
- Font size limitations

## Maintenance Guidelines

### Adding New Styles

1. Follow existing naming conventions
2. Include responsive variations
3. Add accessibility considerations
4. Update validation tests

### Modifying Breakpoints

1. Update breakpoint definitions
2. Test across all screen sizes
3. Verify accessibility compliance
4. Update documentation

### Performance Testing

1. Test with large content
2. Verify smooth transitions
3. Check memory usage
4. Test on various terminals

## Troubleshooting

### Common Issues

1. **Styles not applying**: Check CSS class names match exactly
2. **Layout not responsive**: Verify breakpoint detection
3. **Accessibility issues**: Test with screen readers
4. **Performance problems**: Check for CSS complexity

### Debug Tools

1. Use CSS validation script
2. Check terminal size detection
3. Verify class application
4. Test with different terminals

## Future Enhancements

### Planned Features

- Dynamic color scheme adaptation
- Enhanced animation system
- Better print support
- Extended accessibility features

### Extensibility

The CSS system is designed to be easily extended:

- Add new breakpoints
- Create custom themes
- Extend accessibility features
- Add new component styles

## Contributing

When contributing to the responsive CSS system:

1. Follow existing patterns
2. Include accessibility considerations
3. Add appropriate tests
4. Update documentation
5. Verify cross-terminal compatibility
