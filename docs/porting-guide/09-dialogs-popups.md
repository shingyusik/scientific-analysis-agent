# 9. 다이얼로그 및 팝업 상세

## 9.1 파일 열기 다이얼로그

### 9.1.1 사용 위치

- File → Load Data... (Ctrl+O)

### 9.1.2 설정

```python
file_names, _ = QFileDialog.getOpenFileNames(
    parent=self,
    caption="Load Data",
    directory="",  # 마지막 디렉토리 기억
    filter="VTK Files (*.vtu *.vti *.vtk)"
)
```

### 9.1.3 특징

- **다중 파일 선택 가능**: `getOpenFileNames` 사용
- **필터**: VTK 파일만 표시 (*.vtu, *.vti, *.vtk)
- 다중 파일 선택 시 자동으로 시계열로 처리

---

## 9.2 파일 저장 다이얼로그

### 9.2.1 사용 위치

- Table View → Export to CSV
- Graph View → Export to Image

### 9.2.2 CSV 내보내기

```python
file_path, _ = QFileDialog.getSaveFileName(
    parent=self,
    caption="Export Table Data",
    directory="",
    filter="CSV Files (*.csv);;All Files (*)"
)
```

### 9.2.3 이미지 내보내기

```python
file_path, selected_filter = QFileDialog.getSaveFileName(
    parent=self,
    caption="Export Graph",
    directory="",
    filter="PNG Image (*.png);;"
           "JPEG Image (*.jpg);;"
           "SVG Vector (*.svg);;"
           "PDF Document (*.pdf)"
)
```

---

## 9.3 Scalar Range 다이얼로그

### 9.3.1 용도

스칼라 색상 범위 수동 설정

### 9.3.2 레이아웃

```
┌──────────────────────────────────────┐
│        Custom Scalar Range            │
├──────────────────────────────────────┤
│                                      │
│  Minimum value:  [________0.0_____]  │
│                                      │
│  Maximum value:  [________1.0_____]  │
│                                      │
├──────────────────────────────────────┤
│              [Cancel]  [OK]          │
└──────────────────────────────────────┘
```

### 9.3.3 스핀박스 설정

```python
class ScalarRangeDialog(QDialog):
    def __init__(self, parent, current_min, current_max):
        self.min_spinbox = QDoubleSpinBox()
        self.min_spinbox.setRange(-1e10, 1e10)
        self.min_spinbox.setValue(current_min)
        self.min_spinbox.setDecimals(6)
        self.min_spinbox.setSingleStep(0.1)
        
        self.max_spinbox = QDoubleSpinBox()
        self.max_spinbox.setRange(-1e10, 1e10)
        self.max_spinbox.setValue(current_max)
        self.max_spinbox.setDecimals(6)
        self.max_spinbox.setSingleStep(0.1)
```

### 9.3.4 유효성 검사

```python
def _on_custom_range(self):
    # ...
    min_val, max_val = dialog.get_values()
    
    if min_val >= max_val:
        QMessageBox.critical(self, "Error", 
            "Minimum must be less than maximum.")
        return
```

---

## 9.4 Camera View 다이얼로그

### 9.4.1 용도

카메라 위치, 방향, 줌 수동 설정

### 9.4.2 레이아웃

```
┌──────────────────────────────────────┐
│       Camera View Settings            │
├──────────────────────────────────────┤
│                                      │
│  Position X:    [______1.0000______] │
│  Position Y:    [______1.0000______] │
│  Position Z:    [______1.0000______] │
│                                      │
│  Focal Point X: [______0.0000______] │
│  Focal Point Y: [______0.0000______] │
│  Focal Point Z: [______0.0000______] │
│                                      │
│  View Up X:     [______0.0000______] │
│  View Up Y:     [______0.0000______] │
│  View Up Z:     [______1.0000______] │
│                                      │
│  Zoom / Angle:  [______30.0_______]  │
│                                      │
├──────────────────────────────────────┤
│     [Apply]    [Cancel]    [OK]      │
└──────────────────────────────────────┘
```

### 9.4.3 스핀박스 설정

```python
def _create_spinbox(self, value):
    sb = QDoubleSpinBox()
    sb.setRange(-1e10, 1e10)
    sb.setValue(value)
    sb.setDecimals(4)
    sb.setSingleStep(0.1)
    return sb
```

### 9.4.4 버튼 동작

| 버튼 | 동작 |
|------|------|
| Apply | 현재 값을 적용 (다이얼로그 유지) |
| Cancel | 취소 (변경사항 무시) |
| OK | 적용 후 닫기 |

### 9.4.5 Modal 설정

```python
self.setModal(False)  # 비모달 - 실시간 미리보기 가능
```

---

## 9.5 탭 생성 다이얼로그 (TabCreationDialog)

### 9.5.1 레이아웃

```
┌──────────────────────────────────────┐
│         Create New Tab                │
├──────────────────────────────────────┤
│                                      │
│  Tab Type:  [▼ 3D View        ▼]     │
│                                      │
│  Tab Name:  [____3D View______]      │
│                                      │
├──────────────────────────────────────┤
│             [Cancel]    [OK]          │
└──────────────────────────────────────┘
```

### 9.5.2 타입 선택 시 이름 자동 변경

```python
def _update_default_name(self, tab_type: str):
    """타입 변경 시 기본 이름 자동 설정"""
    default_names = {
        "3D View": "3D View",
        "Table": "Table",
        "Graph": "Graph",
    }
    self._name_edit.setText(default_names.get(tab_type, "Tab"))
```

---

## 9.6 탭 이름 변경 다이얼로그

### 9.6.1 레이아웃

```
┌──────────────────────────────────────┐
│          Rename Tab                   │
├──────────────────────────────────────┤
│                                      │
│  New Name:  [______Table 2______]    │
│                                      │
├──────────────────────────────────────┤
│             [Cancel]    [OK]          │
└──────────────────────────────────────┘
```

### 9.6.2 구현

```python
def _rename_tab(self, tab_id: str):
    metadata = self._tab_metadata.get(tab_id)
    if not metadata:
        return
    
    new_name, ok = QInputDialog.getText(
        self,
        "Rename Tab",
        "New Name:",
        text=metadata['name']
    )
    
    if ok and new_name.strip():
        metadata['name'] = new_name.strip()
        self.setTabText(metadata['index'], new_name.strip())
        self.tab_renamed.emit(tab_id, new_name.strip())
```

---

## 9.7 오프셋 시리즈 생성 다이얼로그 (GenerateSeriesDialog)

### 9.7.1 용도

Slice 필터의 다중 오프셋 값 시리즈 생성

### 9.7.2 레이아웃

```
┌──────────────────────────────────────────────────┐
│           Generate Offset Series                  │
├──────────────────────────────────────────────────┤
│                                                  │
│  Start:    [_______-1.0________]   [Reset Range] │
│  End:      [________1.0________]                 │
│  Count:    [________10_________]                 │
│  Method:   [▼ Linear          ▼]                 │
│                                                  │
│  ── Preview ────────────────────────────         │
│  [-1.0, -0.78, -0.56, -0.33, -0.11, ...]         │
│                                                  │
├──────────────────────────────────────────────────┤
│         [Cancel]    [Generate]    [OK]           │
└──────────────────────────────────────────────────┘
```

### 9.7.3 생성 방법

| 방법 | 설명 |
|------|------|
| Linear | 균등 간격 |
| Logarithmic | 로그 스케일 (구현 예정) |

### 9.7.4 미리보기 업데이트

```python
def _generate_series(self):
    start = self._start_spin.value()
    end = self._end_spin.value()
    count = self._count_spin.value()
    
    self._result = list(np.linspace(start, end, count))
    self._update_preview()

def _update_preview(self):
    """최대 5개까지 미리보기"""
    if len(self._result) > 5:
        preview = self._result[:5]
        text = str([f"{v:.2f}" for v in preview]) + "..."
    else:
        text = str([f"{v:.2f}" for v in self._result])
    
    self._preview_label.setText(text)
```

---

## 9.8 경고/오류 메시지 박스

### 9.8.1 경고 메시지

```python
QMessageBox.warning(
    parent=self,
    title="Warning",
    text="Please select a source in Pipeline Browser."
)
```

### 9.8.2 오류 메시지

```python
QMessageBox.critical(
    parent=self,
    title="Error",
    text="Minimum must be less than maximum."
)
```

### 9.8.3 정보 메시지

```python
QMessageBox.information(
    parent=self,
    title="Export Successful",
    text=f"Data exported to:\n{file_path}"
)
```

---

## 9.9 우클릭 컨텍스트 메뉴

### 9.9.1 Pipeline Browser

```
┌─────────────────────────┐
│ ❌ Delete               │
└─────────────────────────┘
```

### 9.9.2 Table View

```
┌─────────────────────────┐
│ 📥 Export to CSV...     │
└─────────────────────────┘
```

### 9.9.3 Tab Bar

```
┌─────────────────────────┐
│ 📌 Pin Tab              │  (또는 Unpin Tab)
│ ✏️ Rename Tab           │
│ ──────────────────────  │
│ ❌ Close Tab            │
│ 🗑️ Close Other Tabs    │
└─────────────────────────┘
```

---

## 9.10 공통 다이얼로그 스타일

### 9.10.1 폼 레이아웃

```python
layout = QFormLayout(self)
layout.addRow("Label:", widget)
```

### 9.10.2 버튼 박스

```python
# 표준 버튼
buttons = QDialogButtonBox(
    QDialogButtonBox.Ok | QDialogButtonBox.Cancel
)
buttons.accepted.connect(self.accept)
buttons.rejected.connect(self.reject)

# Apply 버튼 추가
buttons = QDialogButtonBox(
    QDialogButtonBox.Apply | QDialogButtonBox.Ok | QDialogButtonBox.Cancel
)
buttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply_clicked)
```

### 9.10.3 모달 설정

```python
self.setModal(True)   # 모달 (다른 윈도우 차단)
self.setModal(False)  # 비모달 (다른 윈도우 접근 가능)
```

---

*다음: [10-filter-system.md](./10-filter-system.md) - 필터 시스템 상세*
