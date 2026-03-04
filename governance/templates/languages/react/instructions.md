# React / TypeScript Instructions

Extends the base AI instructions with React-specific conventions.

## Components

- Functional components only; no class components
- Type props with `interface ComponentNameProps`; export prop types
- Do not use `React.FC` -- type props directly on the function parameter
- Use compound components for related UI groups (Tabs, Select, Accordion)
- Use composition (`children`, render props) over inheritance
- Prefer accessible-by-default component libraries (Radix UI, React Aria, Headless UI)

## TypeScript

- Enable `strict: true` and `noUncheckedIndexedAccess` in tsconfig
- Avoid enums -- use `as const` objects with derived types
- Use discriminated unions for state modeling (`{ status: 'loading' } | { status: 'success'; data: T }`)
- Use `satisfies` for type-checked constants that preserve literal types
- Use `ComponentProps<'button'>` to extract props from existing elements when wrapping
- No `forwardRef` needed in React 19 -- `ref` is a regular prop

## State Management

- `useState` for simple local state; `useReducer` when transitions are complex
- TanStack Query for server state -- separate it completely from client state
- Zustand or Jotai for client global state; avoid Redux in new projects
- React Hook Form + Zod for form state and validation
- URL state (search params, route params) for shareable/bookmarkable state

## Hooks

- Extract reusable stateful logic into custom `use*` hooks
- Follow the Rules of Hooks: top level only, no conditions/loops
- Keep the exhaustive-deps ESLint rule enabled; do not suppress without justification
- `useEffect` is for syncing with external systems only, NOT for derived state or event handling
- Avoid effect chains that set state triggering other effects

## Performance

- Do not prematurely memoize -- profile first
- `React.memo` only for components that re-render frequently with same props and expensive renders
- `useMemo`/`useCallback` sparingly; React Compiler (React Forget) auto-memoizes
- `React.lazy()` + `Suspense` for route-level code splitting
- Use `@tanstack/react-virtual` for long lists
- Lift state down; split contexts for frequently-changing vs stable values
- Use the `children` pattern to prevent unnecessary subtree re-renders

## Project Structure

- Feature-based folders: `src/features/{feature}/` with co-located components, hooks, api, types, tests
- Shared code in `src/shared/` (components, hooks, utils, types)
- Barrel exports only at feature boundaries -- keep them shallow
- Path alias `@/` mapped to `src/` via tsconfig paths
- Co-locate tests and styles with their components

## Testing

- React Testing Library: test behavior, not implementation
- Query priority: `getByRole` > `getByLabelText` > `getByText` > `getByTestId`
- Use `screen` object, not destructured queries
- `user-event` v14+ over `fireEvent` -- use `await userEvent.setup()`
- MSW v2 for API mocking at the network level
- Never test internal state or assert specific function calls
- No snapshot tests unless explicitly justified

## Accessibility

- Semantic HTML first: `<button>`, `<nav>`, `<dialog>`, `<main>` over `<div>` with roles
- All interactive elements must be keyboard accessible
- Trap focus in modals; return focus to trigger on close
- Use `aria-label`, `aria-describedby`, `aria-live` for dynamic content
- Use `eslint-plugin-jsx-a11y` and `axe-core` for automated a11y testing

## Styling

- Tailwind CSS with `clsx` or `tailwind-merge` for conditional classes
- Design tokens as CSS custom properties or Tailwind theme extensions
- Avoid runtime CSS-in-JS (styled-components, Emotion) -- incompatible with Server Components
- For CSS-in-JS: use zero-runtime options (`vanilla-extract`, `Panda CSS`)

## Common Pitfalls

- Inline object/array/function creation in JSX causes unnecessary re-renders of memoized children
- Index as `key` in lists that reorder causes incorrect state preservation
- Stale closures in effects and callbacks -- use refs for "latest value" pattern
- `useEffect` for derived state -- compute during render instead
- Missing cleanup in effects for subscriptions, timers, and event listeners
- Data fetching waterfalls -- fetch at the route level, not deep in the component tree

---

*Extends .ai/instructions.md with React/TypeScript-specific conventions.*
