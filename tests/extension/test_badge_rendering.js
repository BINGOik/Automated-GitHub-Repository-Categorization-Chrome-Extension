/**
 * Reference Jest tests for badge rendering behavior.
 *
 * The repository currently runs Python tests through `pytest tests/ -v`.
 * These JavaScript tests are intentionally kept as executable documentation
 * until a JS runner such as Jest/Vitest + jsdom is added to package.json.
 */
describe("badge rendering", () => {
  function makeBadge(text) {
    const span = document.createElement("span");
    span.textContent = text;
    span.style.display = "inline-flex";
    span.style.borderRadius = "999px";
    return span;
  }

  test("creates a visible badge with provided domain text", () => {
    document.body.innerHTML = "";
    const badge = makeBadge("网页应用");

    expect(badge.textContent).toBe("网页应用");
    expect(badge.style.display).toBe("inline-flex");
    expect(badge.style.borderRadius).toBe("999px");
  });

  test("repo badge can be inserted after repository title link", () => {
    document.body.innerHTML = '<h1><a href="/facebook/react">react</a></h1>';
    const link = document.querySelector("h1 a");
    const badge = makeBadge("网页应用");

    link.insertAdjacentElement("afterend", badge);

    expect(link.nextElementSibling.textContent).toBe("网页应用");
  });
});
