# 11. 사용자 상호작용 논리

## 11.1 마우스 상호작용

### 11.1.1 VTK 렌더 뷰 상호작용

| 입력 | 동작 | VTK Interactor Style |
|------|------|---------------------|
| 좌클릭 + 드래그 | 카메라 회전 (Trackball) | `vtkInteractorStyleTrackballCamera` |
| 우클릭 + 드래그 | 줌 인/아웃 | |
| 중클릭 + 드래그 | 패닝 (Pan) | |
| 휠 스크롤 | 줌 인/아웃 | |
| Shift + 좌클릭 | 패닝 | |

### 11.1.2 회전 동작 상세

```python
# 트랙볼 카메라 회전
# - 마우스 이동 → 구면 좌표 변환
# - 카메라 위치가 구면 위를 따라 이동
# - 초점(focal point)은 고정

def on_mouse_move(self, dx, dy):
    # dx, dy: 마우스 이동량 (픽셀)
    camera = self._renderer.GetActiveCamera()
    
    # 구면 좌표 변환
    azimuth = -dx * 0.5   # 수평 회전
    elevation = -dy * 0.5  # 수직 회전
    
    camera.Azimuth(azimuth)
    camera.Elevation(elevation)
    camera.OrthogonalizeViewUp()
    
    self._renderer.ResetCameraClippingRange()
    self.render()
```

### 11.1.3 줌 동작 상세

```python
def on_zoom(self, factor):
    """
    줌 팩터: > 1 확대, < 1 축소
    - 휠 업: factor = 1.1
    - 휠 다운: factor = 0.9
    """
    camera = self._renderer.GetActiveCamera()
    
    if camera.GetParallelProjection():
        # 평행 투영: 스케일 변경
        camera.SetParallelScale(
            camera.GetParallelScale() / factor
        )
    else:
        # 원근 투영: 줌 (Dolly)
        camera.Dolly(factor)
    
    self._renderer.ResetCameraClippingRange()
    self.render()
```

### 11.1.4 패닝 동작 상세

```python
def on_pan(self, dx, dy):
    """
    dx, dy: 마우스 이동량 (픽셀)
    - 화면 좌표를 월드 좌표로 변환
    - 카메라 위치와 초점 이동
    """
    camera = self._renderer.GetActiveCamera()
    
    # 현재 초점에서 화면 좌표 계산
    focal_point = camera.GetFocalPoint()
    position = camera.GetPosition()
    
    # 화면 이동량을 월드 이동량으로 변환
    # ... 복잡한 변환 로직
    
    camera.SetFocalPoint(new_focal)
    camera.SetPosition(new_position)
    self.render()
```

### 11.1.5 인터랙션 비활성화 상태

```python
def set_interaction_enabled(self, enabled: bool):
    """
    AI 처리 중 인터랙션 비활성화
    """
    if enabled:
        self._interactor.Enable()
        self._orientationWidget.SetEnabled(1)
    else:
        self._interactor.Disable()
        self._orientationWidget.SetEnabled(0)
```

---

## 11.2 키보드 상호작용

### 11.2.1 전역 단축키

| 키 조합 | 위치 | 동작 |
|---------|------|------|
| Ctrl+O | 전역 | 파일 열기 |
| Ctrl+Q | 전역 | 애플리케이션 종료 |
| Enter | 채팅 입력창 | 메시지 전송 |

### 11.2.2 VTK 기본 키 이벤트 (비활성화됨)

```python
# 기본 VTK 키 이벤트는 비활성화
# (의도치 않은 동작 방지)
# 예: 'r' 키로 카메라 리셋 등
```

---

## 11.3 Pipeline Browser 상호작용

### 11.3.1 아이템 선택

```
[트리 아이템 클릭]
         │
         ▼
[QTreeWidget.itemClicked 시그널]
         │
         ▼
[_on_item_clicked 핸들러]
         │
    ┌────┴────┐
    │         │
없음         아이템
    │         │
    ▼         ▼
선택 해제   item_selected.emit(item_id)
```

### 11.3.2 체크박스 토글

```
[체크박스 상태 변경]
         │
         ▼
[QTreeWidget.itemChanged 시그널]
         │
         ▼
[_on_item_changed 핸들러]
         │
         ▼
[CheckState 확인]
         │
    ┌────┴────┐
    │         │
Checked    Unchecked
    │         │
    ▼         ▼
visible=True  visible=False
         │
         ▼
item_visibility_changed.emit(item_id, visible)
```

### 11.3.3 우클릭 메뉴

```python
def contextMenuEvent(self, event):
    item = self.itemAt(event.pos())
    if not item:
        return
    
    menu = QMenu(self)
    delete_action = menu.addAction("Delete")
    delete_action.triggered.connect(
        lambda: self.item_delete_requested.emit(item.data(0, Qt.UserRole))
    )
    menu.exec(event.globalPos())
```

---

## 11.4 Properties Panel 상호작용

### 11.4.1 일반 파라미터 변경

```
[사용자가 SpinBox/ComboBox 값 변경]
         │
         ▼
[valueChanged/currentIndexChanged 시그널]
         │
         ▼
[_on_param_changed 콜백]
         │
         ▼
[현재 파라미터 수집]
         │
         ▼
[on_params_changed 콜백 호출]
         │
         ▼
[filter_params_changed.emit(item_id, params)]
         │
         ▼
[apply_immediately=True인 경우]
    필터 즉시 재적용
         │
         ▼
[렌더 업데이트]
```

### 11.4.2 Apply 버튼 클릭

```
[Apply 버튼 클릭]
         │
         ▼
[apply_filter_requested.emit(item_id)]
         │
         ▼
[PipelineViewModel.commit_filter(item_id)]
         │
         ├──▶ 필터 재계산
         │
         ├──▶ actor 교체
         │
         └──▶ 렌더 업데이트
```

### 11.4.3 Opacity 슬라이더

```python
# 슬라이더 값 변경 시
def _on_opacity_changed(self, value: int):
    opacity = value / OPACITY_SLIDER_MAX  # 0-100 → 0.0-1.0
    self.opacity_changed.emit(self._current_item.id, opacity)

# PipelineViewModel에서 처리
def set_opacity(self, item_id: str, opacity: float):
    item = self.items.get(item_id)
    if item and item.actor:
        item.actor.GetProperty().SetOpacity(opacity)
```

### 11.4.4 Color By 변경

```
[Color By 콤보박스 변경]
         │
         ▼
[currentIndexChanged]
         │
         ▼
[배열 이름, 타입 추출]
         │
    ┌────┴────────┐
    │             │
Solid Color    배열 선택
    │             │
    ▼             ▼
스칼라 비활성화 스칼라 활성화
    │             │
    └─────┬───────┘
          ▼
[color_by_changed.emit(item_id, array_name, array_type, component)]
          │
          ▼
[mapper.SetScalarModeToUsePointFieldData/CellFieldData]
[mapper.SelectColorArray(array_name)]
          │
          ▼
[Scalar Bar 업데이트]
```

---

## 11.5 채팅 패널 상호작용

### 11.5.1 메시지 전송

```
[Enter 키 또는 Send 버튼]
         │
         ▼
[입력창 텍스트 가져오기]
         │
    ┌────┴────┐
    │         │
비어있음     텍스트 있음
    │         │
무시         │
             ▼
      [입력창 클리어]
             │
             ▼
      [message_sent.emit(text)]
             │
             ▼
      [ChatViewModel.send_user_message]
             │
             ▼
      [UI 비활성화]
             │
             ▼
      [에이전트 워커 스레드 시작]
```

### 11.5.2 스트리밍 응답

```
[에이전트에서 토큰 생성]
         │
         ▼
[streaming_token.emit(token)]
         │
         ▼
[ChatPanel.update_streaming]
         │
         ├──▶ 버블 내용 업데이트
         │
         └──▶ 스크롤 하단으로
```

### 11.5.3 Cancel 버튼

```
[Cancel 버튼 클릭]
         │
         ▼
[cancel_requested.emit()]
         │
         ▼
[ChatViewModel.stop_generation]
         │
         ├──▶ 워커 스레드 중단 요청
         │
         ├──▶ 현재 스트리밍 완료 처리
         │
         └──▶ UI 재활성화
```

### 11.5.4 New 버튼

```
[New 버튼 클릭]
         │
         ▼
[new_conversation_requested.emit()]
         │
         ▼
[ChatViewModel.start_new_conversation]
         │
         ├──▶ 채팅 기록 클리어
         │
         ├──▶ 에이전트 상태 초기화
         │
         └──▶ 환영 메시지 표시
```

---

## 11.6 탭 상호작용

### 11.6.1 탭 클릭 (전환)

```
[탭 클릭]
         │
         ▼
[currentChanged 시그널(index)]
         │
         ▼
[MainWindow._on_tab_changed]
         │
         ├──▶ active_tab_id 업데이트
         │
         ├──▶ active_tab_type 업데이트
         │
         ├──▶ Properties Panel 모드 변경
         │
         └──▶ 선택된 아이템으로 탭 콘텐츠 갱신
```

### 11.6.2 탭 닫기 버튼

```
[탭 닫기 버튼(×) 클릭]
         │
         ▼
[tabCloseRequested 시그널(index)]
         │
         ▼
[_on_tab_close_requested]
         │
    ┌────┴────┐
    │         │
고정 탭     일반 탭
    │         │
무시         │
             ▼
      [리소스 정리]
      (VTK: 시그널 연결 해제)
             │
             ▼
      [tab_closed.emit(tab_id)]
```

### 11.6.3 탭 우클릭 메뉴

```
[탭에서 우클릭]
         │
         ▼
[tabBarContextMenuRequested]
         │
         ▼
[컨텍스트 메뉴 표시]
         │
    ┌────┼────┬────┐
    │    │    │    │
 Pin  Rename Close Close
               Tab  Others
```

### 11.6.4 탭 드래그 (재정렬)

```python
# QTabBar의 movable 속성 활성화
self._tab_widget.tabBar().setMovable(True)

# 탭 이동 시 인덱스 매핑 업데이트
def _on_tab_moved(self, from_index: int, to_index: int):
    # 내부 메타데이터 인덱스 갱신
    self._reindex_tabs()
```

---

## 11.7 툴바 상호작용

### 11.7.1 일반 버튼

```
[버튼 클릭]
         │
         ▼
[triggered 시그널]
         │
         ▼
[연결된 콜백 실행]
```

### 11.7.2 드롭다운 버튼

```
[드롭다운 버튼 클릭]
         │
         ▼
[팝업 메뉴 표시]
         │
         ▼
[메뉴 항목 선택]
         │
         ▼
[해당 항목 콜백 실행]
         │
         ▼
[버튼 텍스트 업데이트 (현재 선택 표시)]
```

### 11.7.3 시간 애니메이션 컨트롤

```
[Play 버튼 클릭]
         │
         ▼
[TimeSeriesManager.play_forward/backward]
         │
         ▼
[내부 타이머 시작]
         │
         ▼
[interval_ms 간격으로 time_changed 시그널]
         │
         ▼
[TimeAnimationWidget UI 업데이트]
[파이프라인 아이템 시간 데이터 로드]
[VTK 렌더 업데이트]
```

---

## 11.8 다이얼로그 상호작용

### 11.8.1 모달 다이얼로그

```
[다이얼로그 exec()]
         │
         ▼
[부모 윈도우 블로킹]
         │
         ▼
[사용자 입력]
         │
    ┌────┴────┐
    │         │
 Cancel      OK
    │         │
    ▼         ▼
Rejected   Accepted
    │         │
    └────┬────┘
         │
         ▼
[다이얼로그 닫힘]
[부모 윈도우 활성화]
```

### 11.8.2 Apply/OK/Cancel 패턴

```python
# Apply: 값 적용하지만 다이얼로그 유지
# OK: 값 적용하고 다이얼로그 닫기
# Cancel: 변경 취소하고 다이얼로그 닫기

buttons = QDialogButtonBox(Apply | Ok | Cancel)
buttons.button(Apply).clicked.connect(self._apply)
buttons.accepted.connect(self.accept)
buttons.rejected.connect(self.reject)
```

---

## 11.9 AI 처리 중 상호작용 제한

### 11.9.1 비활성화되는 요소

| 요소 | 비활성화 방법 |
|------|-------------|
| 메뉴바 | `menuBar().setEnabled(False)` |
| 툴바 | `toolbar.setEnabled(False)` |
| Pipeline Browser | `widget.setEnabled(False)` |
| Properties Panel | `widget.setEnabled(False)` |
| Details Tabs | `widget.setEnabled(False)` |
| Tabbed View | `widget.setEnabled(False)` |
| VTK Interactor | `interactor.Disable()` |

### 11.9.2 활성화 유지되는 요소

| 요소 | 이유 |
|------|------|
| 채팅 패널 (부분) | Cancel 버튼 사용 가능 |
| 스크롤 영역 | 채팅 내용 확인 필요 |

### 11.9.3 시각적 피드백

```python
# 대기 커서 표시
QApplication.setOverrideCursor(Qt.WaitCursor)

# 복원 (모든 오버라이드 제거)
while QApplication.overrideCursor() is not None:
    QApplication.restoreOverrideCursor()
```

---

*다음: [12-data-flow-architecture.md](./12-data-flow-architecture.md) - 데이터 흐름 및 아키텍처*
