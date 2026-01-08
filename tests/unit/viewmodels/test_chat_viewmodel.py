
import pytest
from unittest.mock import MagicMock, patch, ANY
from PySide6.QtCore import QObject
from viewmodels.chat_viewmodel import ChatViewModel, ChatMessage, StreamingAgentWorker

@pytest.fixture
def chat_vm(qapp):
    # Mock dependencies
    pipeline_vm = MagicMock()
    vtk_vm = MagicMock()
    
    # Mock Config to ensure agent initializes (or we can mock create_agent directly)
    with patch("viewmodels.chat_viewmodel.Config") as mock_config:
        mock_config.is_configured.return_value = True
        
        with patch("viewmodels.chat_viewmodel.create_agent") as mock_create_agent:
            mock_agent = MagicMock()
            mock_create_agent.return_value = mock_agent
            
            vm = ChatViewModel(pipeline_vm, vtk_vm)
            vm.initialize_agent() # Initialize agent for tests
            yield vm

def test_initial_state(chat_vm):
    assert len(chat_vm.messages) == 0
    assert chat_vm.is_agent_available is True

def test_add_system_message(chat_vm):
    mock_slot = MagicMock()
    chat_vm.message_added.connect(mock_slot)
    
    chat_vm.add_system_message("System Init")
    
    assert len(chat_vm.messages) == 1
    assert chat_vm.messages[0].sender == "System"
    assert chat_vm.messages[0].content == "System Init"
    mock_slot.assert_called_once()

def test_send_user_message_starts_processing(chat_vm):
    # Mock _process_with_agent to verify it's called
    with patch.object(chat_vm, "_process_with_agent") as mock_process:
        chat_vm.send_user_message("Hello")
        
        assert len(chat_vm.messages) == 1
        assert chat_vm.messages[0].sender == "User"
        mock_process.assert_called_once()

@patch("viewmodels.chat_viewmodel.StreamingAgentWorker")
def test_process_with_agent_starts_worker(mock_worker_cls, chat_vm):
    mock_worker = MagicMock()
    mock_worker_cls.return_value = mock_worker
    
    # Mock dependencies logic
    chat_vm._messages = [ChatMessage("User", "Hi")]
    
    chat_vm._process_with_agent()
    
    # Check worker initialization
    mock_worker_cls.assert_called_once()
    mock_worker.start.assert_called_once()
    assert chat_vm._worker == mock_worker

def test_stop_generation(chat_vm):
    mock_worker = MagicMock()
    mock_worker.isRunning.return_value = True
    chat_vm._worker = mock_worker
    
    chat_vm.stop_generation()
    
    mock_worker.stop.assert_called_once()
    # It attempts to disconnect signals, which might fail if not connected, but handled in try/except

def test_streaming_lifecycle(chat_vm):
    # Simulate streaming flow manually by invoking callbacks
    
    # 1. Token received
    mock_token_signal = MagicMock()
    chat_vm.streaming_token.connect(mock_token_signal)
    
    chat_vm._on_token_received("H")
    chat_vm._on_token_received("i")
    
    assert chat_vm._current_response == "Hi"
    mock_token_signal.assert_any_call("Hi")
    
    # 2. Finished
    mock_finished_signal = MagicMock()
    chat_vm.streaming_finished.connect(mock_finished_signal)
    
    state = {"blocked": False}
    chat_vm._on_streaming_finished(state)
    
    assert len(chat_vm.messages) == 1
    assert chat_vm.messages[0].sender == "Agent"
    assert chat_vm.messages[0].content == "Hi"
    mock_finished_signal.assert_called_once()

def test_clear_history(chat_vm):
    chat_vm.add_system_message("Test")
    assert len(chat_vm.messages) == 1
    
    mock_signal = MagicMock()
    chat_vm.conversation_cleared.connect(mock_signal)
    
    chat_vm.start_new_conversation()
    
    assert len(chat_vm.messages) == 0
    mock_signal.assert_called_once()
