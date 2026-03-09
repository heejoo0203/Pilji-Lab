export default function AccountDeletionPage() {
  return (
    <>
      <section className="panel">
        <h2>계정 삭제 안내</h2>
        <p className="hint">
          앱 이름: <strong>필지랩</strong>
          <br />
          개발자: <strong>heejoo0203</strong>
        </p>
        <p className="hint">
          필지랩 계정 삭제는 앱/웹에서 직접 요청할 수 있으며, 요청 시 관련 데이터는 아래 정책에 따라 삭제 또는 보관됩니다.
        </p>
      </section>

      <section className="panel privacy-section">
        <h3>1. 계정 삭제 요청 방법</h3>
        <ol className="privacy-ordered-list">
          <li>
            필지랩 로그인 후 <strong>마이페이지</strong>로 이동
          </li>
          <li>
            <strong>회원 탈퇴</strong> 영역에서 안내 문구를 정확히 입력
          </li>
          <li>
            <strong>회원 탈퇴</strong> 버튼을 눌러 삭제 요청 완료
          </li>
        </ol>
        <p className="hint">
          로그인 불가 등으로 앱에서 삭제가 어려운 경우 아래 이메일로 요청할 수 있습니다.
          <br />
          문의: <a href="mailto:kr.autolv@gmail.com">kr.autolv@gmail.com</a>
        </p>
      </section>

      <section className="panel privacy-section">
        <h3>2. 삭제되는 데이터</h3>
        <ul>
          <li>회원 계정 정보(이름, 연락처, 이메일, 프로필 이미지)</li>
          <li>사용자별 조회기록(개별조회/지도조회)</li>
          <li>파일조회 작업 이력 및 업로드/결과 파일</li>
          <li>인증 관련 세션/토큰 정보</li>
        </ul>
      </section>

      <section className="panel privacy-section">
        <h3>3. 보관되는 데이터 및 기간</h3>
        <ul>
          <li>법령상 보관이 필요한 정보가 있는 경우 해당 법령에서 정한 기간 동안 보관 후 파기</li>
          <li>보안/장애 대응 목적의 시스템 로그는 최대 90일 내에서 보관 후 자동 삭제될 수 있음</li>
          <li>계정 삭제 완료 이후에는 사용자 식별이 가능한 서비스 데이터 복구 불가</li>
        </ul>
      </section>

      <section className="panel privacy-section">
        <h3>4. 처리 기한</h3>
        <p className="hint">
          앱/웹에서 회원 탈퇴를 완료한 경우 즉시 서비스 접근이 차단되며, 내부 정리 작업은 통상 지체 없이 처리됩니다.
        </p>
      </section>
    </>
  );
}
