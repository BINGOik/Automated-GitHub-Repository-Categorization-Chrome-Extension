/**
 * Reference Jest tests for GitHub owner/repo parsing behavior.
 *
 * The active CI command in this project is `pytest tests/ -v`; the Python
 * static tests verify that content.js contains the same parsing constraints.
 */
describe("content parser", () => {
  function parseOwnerRepoFromHref(href) {
    const url = href.startsWith("http")
      ? new URL(href)
      : new URL(href, "https://github.com");
    if (url.hostname !== "github.com") return null;
    const parts = url.pathname.split("/").filter(Boolean);
    if (parts.length !== 2) return null;
    return { owner: parts[0], repo: parts[1] };
  }

  test("parses exact /owner/repo links", () => {
    expect(parseOwnerRepoFromHref("/facebook/react")).toEqual({
      owner: "facebook",
      repo: "react",
    });
  });

  test("rejects nested repository paths", () => {
    expect(parseOwnerRepoFromHref("/facebook/react/issues")).toBeNull();
  });
});
