import fs from "node:fs";
import path from "node:path";

const root = process.cwd();

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), "utf8");
}

function assertIncludes(source, snippet, description) {
  if (!source.includes(snippet)) {
    throw new Error(`Regression check failed: ${description}`);
  }
}

const mapDrawer = read("app/components/map/map-result-drawer.tsx");
const mapRowsTable = read("app/components/map/map-rows-table.tsx");
const searchPage = read("app/(main)/search/page.tsx");
const filesPage = read("app/(main)/files/page.tsx");
const historyPage = read("app/(main)/history/page.tsx");
const myPage = read("app/(main)/mypage/page.tsx");
const bulkJobTable = read("app/components/files/bulk-job-table.tsx");
const brandRefresh = read("app/brand-refresh.css");

assertIncludes(
  mapDrawer,
  'const drawerHandleLabel = open ? "패널 닫기" : "결과 보기";',
  "map drawer handle label should keep the requested '결과 보기' state",
);
assertIncludes(
  mapRowsTable,
  'return `${Number(match[1])}/${Number(match[2])}`;',
  "map yearly table should normalize base dates to M/D",
);
assertIncludes(
  searchPage,
  "formatBaseDate(row.기준일자)",
  "search yearly table should normalize base dates to M/D",
);
assertIncludes(
  filesPage,
  "new Set(filteredJobs.map((job) => job.job_id))",
  "files select-all should only target currently filtered jobs",
);
assertIncludes(
  filesPage,
  "[page, statusFilter]",
  "files selection should reset when page or filter changes",
);
assertIncludes(
  historyPage,
  "setTotalCount(payload.total_count);",
  "history page should expose total record count from API",
);
assertIncludes(
  historyPage,
  '<span>현재 결과</span>',
  "history page should distinguish total count from filtered result count",
);
assertIncludes(
  historyPage,
  "restoreRecord(row)",
  "history page should provide an explicit restore action for each row",
);
assertIncludes(
  bulkJobTable,
  "buildPaginationItems(props.page, props.totalPages)",
  "bulk job table should use condensed pagination items instead of rendering every page button",
);
assertIncludes(
  myPage,
  'const [activeAction, setActiveAction] = useState<null | "profile" | "password" | "withdrawal">(null);',
  "mypage should track which account action is currently running",
);
assertIncludes(
  myPage,
  'authLoading && activeAction === "withdrawal" ? "탈퇴 처리 중..." : "회원 탈퇴"',
  "mypage withdrawal button should show action-specific loading state",
);
assertIncludes(
  myPage,
  'const androidApkPath = "/downloads/autoLV-android-release-v2.2.0.apk";',
  "mypage should point users to the current Android APK version",
);
assertIncludes(
  brandRefresh,
  ".lab-btn.full,",
  "lab button full-width modifier should be styled for mypage and other CTA buttons",
);

console.log("ui-regression-check: ok");
