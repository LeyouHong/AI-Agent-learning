import json
import os
from pathlib import Path
import pickle, base64
from typing import Any, Optional, Sequence
from app.code_agent.model.chat_gpt_model import llm_gpt
from app.code_agent.tools.file_tools import file_toolskit

from langgraph.checkpoint.base import BaseCheckpointSaver, ChannelVersions, Checkpoint, CheckpointMetadata, CheckpointTuple
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent

from app.common import FILE_DIR

class FileSaver(BaseCheckpointSaver[str]):
    def __init__(
        self,
        base_path: Path = Path(FILE_DIR) / "checkpoint"
    ):
        super().__init__()
        self.base_path = base_path

        os.makedirs(base_path, exist_ok=True)

    def _get_checkpoint_path(self, thread_id, checkpoint_id):
        dir_path = os.path.join(self.base_path, thread_id)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, f"{checkpoint_id}.json")
        return file_path
    
    def _serialize_checkpoint(self, data) -> str:
        pickled = pickle.dumps(data)
        return base64.b64encode(pickled).decode("utf-8")
    
    def _deserialize_data(self, data):
        decoded = base64.b64decode(data)
        return pickle.loads(decoded)

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Fetch a checkpoint tuple using the given configuration.

        Args:
            config: Configuration specifying which checkpoint to retrieve.

        Returns:
            The requested checkpoint tuple, or `None` if not found.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        # 1. find correct checkpoint file path
        thread_id = config["configurable"]["thread_id"]
        
        # 2.read checkpoint file
        dir_path = os.path.join(self.base_path, thread_id)
        checkpoint_files = list(Path(dir_path).glob("*.json"))
        checkpoint_files.sort(key=lambda x: x.stem, reverse=True)
        if len(checkpoint_files) > 0:
            latest_checkpoint = checkpoint_files[0]
            checkpoint_id = latest_checkpoint.stem
            checkpoint_file_path = self._get_checkpoint_path(thread_id, checkpoint_id)

            # 3. deserialize checkpoint and metadata
            with open(checkpoint_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            checkpoint = self._deserialize_data(data["checkpoint"])
            metadata = self._deserialize_data(data["metadata"])

            # 4. return
            return CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_id": checkpoint_id
                    }
                },
                checkpoint=checkpoint,
                metadata=metadata,
            )
        else:
            return None
    
    def put(
            self,
            config: RunnableConfig,
            checkpoint: Checkpoint,
            metadata: CheckpointMetadata,
            new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Store a checkpoint with its configuration and metadata.

        Args:
            config: Configuration for the checkpoint.
            checkpoint: The checkpoint to store.
            metadata: Additional metadata for the checkpoint.
            new_versions: New channel versions as of this write.

        Returns:
            RunnableConfig: Updated configuration after storing the checkpoint.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        # create a path for saving the checkpoint
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]

        checkpoint_path = self._get_checkpoint_path(thread_id, checkpoint_id)

        # Serialize the checkpoint.
        checkpoint_data = {
            "checkpoint": self._serialize_checkpoint(checkpoint),
            "metadata": self._serialize_checkpoint(metadata),
        }

        # save the checkpoint to the file system
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

        # return
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id
            },
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Store intermediate writes linked to a checkpoint.

        Args:
            config: Configuration of the related checkpoint.
            writes: List of writes to store.
            task_id: Identifier for the task creating the writes.
            task_path: Path of the task creating the writes.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        print("put_writes")

if __name__ == "__main__":
    saver = FileSaver()
    config = RunnableConfig(configurable={"thread_id": 2})

    agent = create_react_agent(
        model=llm_gpt, 
        tools=file_toolskit, 
        checkpointer=saver,
    )

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit" or user_input.lower() == "quit":
            break
        resp = agent.invoke(input={"messages": [
            ("user", user_input)
        ]}, config=config)

        print("AI: ", resp["messages"][-1].content)
        print()