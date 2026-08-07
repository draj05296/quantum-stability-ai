// Builds a compact page-number list for the table pager, e.g. for
// currentPage=5, totalPages=31 this returns [1, "…", 4, 5, 6, "…", 31]
// instead of rendering all 31 page buttons.
export function getPageNumbers(currentPage, totalPages) {
  const delta = 1;
  const pages = [];

  for (let page = 1; page <= totalPages; page += 1) {
    if (
      page === 1 ||
      page === totalPages ||
      (page >= currentPage - delta && page <= currentPage + delta)
    ) {
      pages.push(page);
    }
  }

  const pagesWithEllipsis = [];
  let previousPage;

  pages.forEach((page) => {
    if (previousPage) {
      if (page - previousPage === 2) {
        pagesWithEllipsis.push(previousPage + 1);
      } else if (page - previousPage > 2) {
        pagesWithEllipsis.push("…");
      }
    }
    pagesWithEllipsis.push(page);
    previousPage = page;
  });

  return pagesWithEllipsis;
}
