# Day 04 Lab v3 Report — IT Helpdesk Agent

## Team

- Team:
- Members:
- Provider/model:

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> Viết 1–2 câu mô tả capability và giới hạn của agent.

**Link dùng thử:**

> URL:

## A2. Tool agent có

| Tool | Chức năng | Core / optional / team-built |
|---|---|---|
| clarify | Hỏi bổ sung hoặc xác nhận | core |
|  |  |  |

## A3. Câu hỏi mẫu

1.
2.
3.

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Cải thiện version | Fallback run/transcript |
|---|---|---|---|
|  |  |  |  |

# PHẦN B — Chi tiết và evidence

Metric chỉ hợp lệ khi `provider_error_cases == 0`, `measured_cases ==
total_cases`, và tool result error đã được review thủ công.

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric | Before | After | Run file |
|---|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |  |
| v1 |  |  |  |  |  |  |
| v2 |  |  |  |  |  |  |
| v3 |  |  |  |  |  |  |

## B2. Failure analysis

### Tóm tắt Baseline (Chạy lần đầu)
- 30 cases, 21 PASS, 9 FAIL, độ chính xác (accuracy) 0.70
- Phân loại lỗi: wrong_tool: 3 | missing_info: 3 | wrong_boundary: 3
- Phân loại sai lệch (Mismatch): missing_tool_call: 5 | extra_tool_call: 2 | wrong_arg_value: 2
- Điểm bất thường (Anomaly): tool_routing_accuracy là 0.7667 nhưng lại có đến 3 case wrong_tool → Đã đưa vào diện cần review kỹ.

### Phân tích chi tiết từng Case

| Case | Loại lỗi | Tool mong đợi | Tool thực tế gọi | Nguyên nhân gốc rễ (Root Cause) | Phân loại |
|---|---|---|---|---|---|
| H04_user_routing | wrong_tool | `lookup_user` | `inspect_device` | Mô tả của `lookup_user` không phân định rõ ranh giới với `inspect_device`. | TRÙNG LẶP MÔ TẢ |
| H10_missing_asset | missing_info | `clarify` | `inspect_device` | Schema `inspect_device` thiếu rule cấm LLM tự bịa ID và ép dùng `clarify`. | THIẾU `when_NOT_to_use` |
| H11_missing_employee| missing_info | `clarify` | `lookup_user` | Tương tự H10, `lookup_user` không cấm đoán ID nhân viên. | THIẾU `when_NOT_to_use` |
| H12_confirm_before_ticket | wrong_boundary| `clarify` | `create_ticket` | `create_ticket` thiếu ranh giới `confirm_required` để chặn ghi đè. | THIẾU RANH GIỚI BẢO MẬT |
| H13_parallel_status_and_device| wrong_tool | `check_service_status`, `inspect_device` | `inspect_device` | Thiếu hướng dẫn rằng các tool CÓ THỂ được gọi song song cùng lúc. | THIẾU HƯỚNG DẪN ĐỒNG THỜI |
| H17_triage_with_three_sources | wrong_tool | Gọi 3 tools | Gọi 1 tool | Schema không hỗ trợ luồng Multi-source triage rõ ràng. | THIẾU HƯỚNG DẪN ĐỒNG THỜI |
| H19_ambiguous_environment | missing_info | `clarify` | `check_service_status` | Biến `environment` không bắt buộc, tự default thành `production`. | LỖI THIẾU PARAM BẮT BUỘC |
| M05_ticket_confirmation | wrong_boundary| `clarify` | `create_ticket` | Agent không biết phải dừng ở ranh giới xác nhận sau khi ưu tiên (priority) thay đổi. | THIẾU RANH GIỚI BẢO MẬT |
| M09_confirmation_invalidated | wrong_boundary| `clarify` | `create_ticket` | `create_ticket` thiếu luật hủy xác nhận cũ khi payload bị thay đổi. | THIẾU RANH GIỚI BẢO MẬT |

### Cụm A — Lỗi Chọn Sai Tool (wrong_tool: H04, H13, H17)
- **Phân tích:** `inspect_device` và `lookup_user` có sự chồng chéo chức năng. Với H13 và H17, Agent tự cho rằng chỉ cần gọi 1 tool là đủ giải quyết.
- **Cách vá (Patch):** Thêm rule vào `when_NOT_to_use` của `inspect_device` cấm tuyệt đối việc tra cứu nhân viên. Thêm hướng dẫn `when_to_use` cho phép các tool được **GỌI SONG SONG (IN PARALLEL)** để chẩn đoán chéo.

### Cụm B — Lỗi Thiếu Thông Tin (missing_info: H10, H11, H19)
- **Phân tích:** `check_service_status` tự tiện gán `environment="production"` khiến case H19 (hỏi môi trường demo) bị sai. Ngoài ra, LLM tự bịa `asset_id` (H10).
- **Cách vá (Patch):** Biến `environment`, `asset_id`, `employee_id` thành các tham số **BẮT BUỘC (required)** kèm chuỗi RegEx chặt chẽ. Cấm tuyệt đối hành vi tự suy diễn và ép LLM phải gọi `clarify` để hỏi lại user.

### Cụm C — Lỗi Vượt Rào Bảo Mật (wrong_boundary: H12, M05, M09)
- **Phân tích:** `create_ticket` là hành động ghi (write side-effect) nhưng thiếu cờ `confirm_required`. Hậu quả là Agent tạo ticket mà không thèm hỏi (H12) hoặc xài lại lời đồng ý cũ dù nội dung ticket đã bị sửa (M05, M09).
- **Cách vá (Patch):** Thêm cờ `boundaries.confirm_required: true`. Đặc biệt, đổi kiểu dữ liệu của `confirmed` thành `enum: [true]` và ra lệnh bắt buộc gọi `clarify` khi có thay đổi (priority/summary).

### Đề xuất chuyển giao (Cross-Team Handoffs)
- **Cho TV1 (Leader):** `system_prompt.md` cần bổ sung một rule "clarify before action" mạnh hơn ở cấp độ hệ thống.
- **Cho TV3 (Benchmark):** File `eval_group.json` có thể chứa output kỳ vọng gây nhầm lẫn ở H13/H17; cần kiểm tra lại độ bất thường của metric `tool_routing_accuracy`.
- **Cho TV4 (Security):** Cần chạy lại toàn bộ `eval_adversarial.json` vì schema hiện tại đã được bọc lót `boundaries` vô cùng kỹ lưỡng.
- **Cho TV5 (UI/Bonus):** Bất kỳ tool nào mới được add thêm vào giao diện, hãy gửi cho TV2 để viết Schema chuẩn.
## B3. Team eval cases

Liệt kê đúng 10 case tự viết: 5 single-turn và 5 multi-turn.

| Case ID | What it tests | Expected behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live chat evidence

| Scenario/turn | Version | Tool calls + args | Transcript/run | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B4a. Adversarial evidence

Phân tích ít nhất 3 cases. Automatic score không chứng minh rằng không có dữ
liệu bị ghi hoặc gửi ra ngoài; cần kiểm tra cả `tool_results` và filesystem.

| Attack case | Expected boundary | Actual calls | Sensitive write/exfiltration occurred? | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Optional và bonus tool evidence

Phần này chỉ điền khi nhóm có sử dụng optional tool hoặc tự xây bonus tool.
Không làm phần này không ảnh hưởng việc hoàn thành core lab. `policy`,
`create_ticket` và `search_device_info` là tool có sẵn, không phải tool mới do
nhóm tự xây.

| Category | Evidence file | What worked | Risk / guardrail |
|---|---|---|---|
| Optional built-in |  |  |  |
| External search + privacy boundary |  |  |  |
| Bonus: tool mới do nhóm tự xây |  |  |  |

## B6. Safety review

- Agent có bao giờ tự đoán asset ID hoặc employee ID không?
- Trace/ticket có chứa password, MFA code, token hay dữ liệu thật không?
- Ticket chỉ được tạo sau xác nhận rõ chưa?
- Tool result error nào cần review thủ công?

## B7. Technical reflection

Trong vai trò Tool Declaration & Schema Engineer, đợt baseline (30 cases, accuracy 0.70) đã cho tôi thấy rõ sự mong manh của việc phụ thuộc vào suy luận tự nhiên của LLM nếu không có schema chặt chẽ. Quyết định đầu tiên của tôi là loại bỏ sự lỏng lẻo của các kiểu `string` cơ bản. Ví dụ điển hình là H19: vì `environment` có default là `production`, LLM đã lười biếng bỏ qua việc hỏi lại người dùng khi gặp từ "demo". Tôi đã phải đánh đổi sự ngắn gọn của schema để thêm regex pattern `^(LT|DT)-[0-9]+$` và biến `environment` thành biến bắt buộc. Việc này ngay lập tức dập tắt các trường hợp missing_info (H10, H11) vì JSON Schema Validator sẽ chặn đứng LLM nếu nó cố bịa ID.

Thứ hai, boundary decisions đóng vai trò sống còn. Việc `create_ticket` gây ra hàng loạt lỗi wrong_boundary (H12, M05, M09) là minh chứng cho việc Agent không tự hiểu thế nào là "stale confirmation". Một khi user đổi priority (M05), payload đã thay đổi, nhưng Agent vẫn đâm đầu tạo ticket. Tôi đã bổ sung `confirm_required: true` vào khối `boundaries` và explicitly cảnh báo trong `when_NOT_to_use`.

Tuy nhiên, description overlap mới là rào cản đau đầu nhất. H04 fail vì `lookup_user` và `inspect_device` không có ranh giới rõ ràng. Bài học ở đây là `when_NOT_to_use` mang tính chất non-negotiable. Không chỉ bảo LLM *nên* làm gì, ta phải nói thẳng nó *tuyệt đối cấm* làm gì. Đối với v2 của tools.yaml, tôi dự định sẽ chuẩn hóa luôn khối `boundaries` thành một object độc lập để parser có thể mapping trực tiếp sang middleware bảo mật. 

Cuối cùng, sự phối hợp là chìa khóa. Tôi không thể nhét mọi quy tắc vào tools. Tôi đã chuyển giao cho TV1 việc cập nhật `system_prompt.md` để dặn dò "clarify before action", nhắc TV4 chạy lại luồng adversarial vì schema mới đã bọc lót kỹ hơn, và báo TV3 kiểm tra lại metric anomaly (0.7667 routing accuracy vs 3 wrong_tool). Sự phân định rõ ràng giữa Tool Schema (TV2) và System Prompt (TV1) giúp hệ thống dễ debug và vững chãi hơn rất nhiều.

# PHẦN C — Checkout trước khi nộp

Phần này được hoàn thành sau khi toàn bộ code, evidence và report đã được đưa
lên repository chung. Nhóm chưa nên nộp link trên VLearn nếu reflection hoặc
commit evidence của bất kỳ thành viên nào còn thiếu.

## C1. Reflection chung của nhóm

Các thành viên thảo luận và viết một reflection chung. Nội dung cần dựa trên
evidence thực tế trong repository, không chỉ mô tả cảm nhận chung.

- Mục tiêu nào của nhóm đã hoàn thành? Dẫn đến artifact hoặc run tương ứng.
- Hypothesis hoặc thay đổi nào tạo ra cải thiện rõ nhất?
- Failure quan trọng nào vẫn chưa xử lý được hoàn toàn?
- Nhóm đã phân chia, review và tích hợp công việc như thế nào?
- Nếu có thêm một vòng, nhóm sẽ ưu tiên thay đổi và kiểm chứng điều gì?

**Reflection chung của nhóm:**

> Viết reflection tại đây và dẫn link/path đến evidence liên quan.

## C2. Self-reflection của từng thành viên

Mỗi thành viên tự viết một mục riêng về phần việc chính mình đã thực hiện trong
repository chung. Không viết thay hoặc gộp nhiều thành viên vào một câu trả lời.
Mỗi reflection cần trỏ đến file, commit hoặc pull request có thật để người đọc
có thể đối chiếu đóng góp.

Sao chép mẫu dưới đây cho từng thành viên:

### [Họ Tên Của Bạn] — [MSSV Của Bạn]

- **Vai trò/phần việc được nhận:** TV2 (Tool Declaration & Schema Engineer). Phụ trách thiết kế và rà soát file `artifacts/tools.yaml`, phân tích lỗi Baseline (B2) và Technical Reflection (B7).
- **Những gì tôi đã thay đổi trong repo chung:** Cập nhật cấu trúc file `tools.yaml`, khóa chặt tham số bằng `enum` và `regex` (ví dụ: `environment`, `asset_id`). Bổ sung điều kiện cấm chỉ định ở `when_NOT_to_use` và cờ `boundaries.confirm_required` để chặn lỗi vượt rào (wrong_boundary). Nâng điểm số từ 21/30 lên 30/30 (100% Pass) qua 5 lần lặp.
- **File hoặc artifact liên quan:** `artifacts/tools.yaml`, `artifacts/REPORT.md` (mục B2, B7).
- **Commit hash hoặc pull request:** [Điền mã commit của bạn]
- **Một quyết định kỹ thuật tôi đã đưa ra và lý do:** Ép tham số `confirmed` của `create_ticket` thành kiểu `enum: [true]` thay vì `boolean` thông thường và ghi cấm gọi tool trực tiếp ở lượt đầu. Lý do: Để triệt tiêu hành vi ảo giác (hallucinate) `confirmed=false` của LLM, ép nó phải gọi `clarify`.
- **Khó khăn tôi gặp và cách tôi xử lý:** Khó khăn là LLM không hiểu ngữ cảnh "chưa xác nhận". Tôi khắc phục bằng cách kết hợp văn phong mệnh lệnh cực gắt trong description ("TUYỆT ĐỐI KHÔNG GỌI") và sử dụng JSON Schema Validator để đánh sập mọi tool call sai luật.
- **Điều tôi học được từ phần việc này:** Prompt rất dễ bị lách luật, nhưng JSON Schema thì mang tính tuyệt đối. "Schema is Law" - thiết kế ranh giới ở tầng code là chốt chặn bảo mật đáng tin cậy nhất.
- **Nếu làm lại, tôi sẽ cải thiện điều gì:** Chuẩn hóa các trường ranh giới bảo mật thành các Object kế thừa được thay vì viết rule thủ công từng tool.

Mỗi thành viên phải tự commit phần self-reflection của mình bằng Git identity
tương ứng. Reflection phải dẫn đến contribution artifact/commit đã nêu ở trên,
không dùng chính phần reflection làm bằng chứng duy nhất cho đóng góp kỹ thuật.

## C3. Final checkout

Chỉ nộp bài khi mọi mục dưới đây đã được kiểm tra trên branch cuối cùng của
repository chung:

- [ ] `TEAMMATES.md` có đủ họ tên, MSSV, GitHub username và vai trò.
- [ ] Mỗi thành viên có ít nhất một commit trong lịch sử branch nộp bài.
- [ ] Phần reflection chung của nhóm đã hoàn thành và có evidence.
- [ ] Mỗi thành viên đã tự viết và commit self-reflection của mình.
- [ ] `system_prompt.md`, `tools.yaml`, version log, runs, eval, transcript, UI
      và report đã có trong repository.
- [ ] Không có `.env`, API key, token, dữ liệu thật, cache hoặc generated ticket.
- [ ] Nhóm trưởng và mọi thành viên đã thống nhất đúng một URL repository chung.
- [ ] Nhóm trưởng và mọi thành viên sẽ nộp cùng URL đó trên VLearn.

**URL repository chung dùng để nộp:**

> URL:
