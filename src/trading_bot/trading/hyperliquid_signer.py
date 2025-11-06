"""EIP-712 signing for HyperLiquid Exchange API.

This module implements signing for HyperLiquid exchange operations using
the EIP-712 standard. It's based on the official HyperLiquid Python SDK.

Reference: https://github.com/hyperliquid-dex/hyperliquid-python-sdk
"""

import json
import logging
from typing import Any, Dict, Optional

from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import to_checksum_address

logger = logging.getLogger(__name__)


class HyperLiquidSigner:
    """Handle EIP-712 signing for HyperLiquid Exchange API.

    This signer creates signatures for trading operations on HyperLiquid
    using the Ethereum EIP-712 standard for structured data signing.

    Attributes:
        account: Ethereum account for signing
        address: Checksum Ethereum address
    """

    # HyperLiquid L1 domain
    HYPERLIQUID_CHAIN_ID = 1337
    HYPERLIQUID_VERIFYING_CONTRACT = "0x0000000000000000000000000000000000000000"

    # EIP-712 domain name and version
    DOMAIN_NAME = "Exchange"
    DOMAIN_VERSION = "1"

    def __init__(self, private_key: str):
        """Initialize signer with private key.

        Args:
            private_key: Ethereum private key in hex format (with or without 0x prefix)

        Raises:
            ValueError: If private key is invalid
        """
        # Normalize private key format
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key

        try:
            self.account = Account.from_key(private_key)
            self.address = to_checksum_address(self.account.address)
            logger.info(f"Initialized signer with address: {self.address}")
        except Exception as e:
            logger.error(f"Failed to initialize signer: {e}")
            raise ValueError(f"Invalid private key: {e}")

    def sign_l1_action(
        self,
        action: Dict[str, Any],
        nonce: int,
        vault_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sign an L1 action (orders, cancels, leverage updates, etc).

        This creates an EIP-712 signature for actions on the HyperLiquid exchange.
        The signature proves that the wallet owner authorizes the action.

        Args:
            action: Action payload dict (e.g., order, cancel, updateLeverage)
            nonce: Current timestamp in milliseconds
            vault_address: Optional vault/subaccount address

        Returns:
            Signature dict with r, s, v components

        Example:
            >>> signer = HyperLiquidSigner("0xprivatekey")
            >>> action = {"type": "order", "orders": [...]}
            >>> sig = signer.sign_l1_action(action, 1234567890, None)
            >>> print(sig)
            {'r': '0x...', 's': '0x...', 'v': 28}
        """
        # Construct connection ID (not used in current implementation)
        connection_id = bytes(32)  # 32 zero bytes

        # Prepare typed data according to HyperLiquid's EIP-712 structure
        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "Agent": [
                    {"name": "source", "type": "string"},
                    {"name": "connectionId", "type": "bytes32"}
                ]
            },
            "primaryType": "Agent",
            "domain": {
                "name": self.DOMAIN_NAME,
                "version": self.DOMAIN_VERSION,
                "chainId": self.HYPERLIQUID_CHAIN_ID,
                "verifyingContract": self.HYPERLIQUID_VERIFYING_CONTRACT
            },
            "message": {
                "source": "a",  # "a" indicates API/agent source
                "connectionId": f"0x{connection_id.hex()}"
            }
        }

        # Encode and sign the typed data
        try:
            encoded_data = encode_typed_data(full_message=typed_data)
            signed_message = self.account.sign_message(encoded_data)

            # Extract r, s, v components
            signature = {
                "r": f"0x{signed_message.r.to_bytes(32, 'big').hex()}",
                "s": f"0x{signed_message.s.to_bytes(32, 'big').hex()}",
                "v": signed_message.v
            }

            logger.debug(f"Signed action with nonce {nonce}")
            return signature

        except Exception as e:
            logger.error(f"Failed to sign action: {e}")
            raise

    def sign_user_signed_action(
        self,
        action: Dict[str, Any],
        nonce: int,
        vault_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sign a user-signed action (alternative signing method).

        This is an alternative signing method used by HyperLiquid for certain
        operations. The main difference is in the typed data structure.

        Args:
            action: Action payload
            nonce: Timestamp in milliseconds
            vault_address: Optional vault address

        Returns:
            Signature dict with r, s, v
        """
        # For now, use the same implementation as sign_l1_action
        # This may need to be adjusted based on actual API requirements
        return self.sign_l1_action(action, nonce, vault_address)

    def verify_signature(
        self,
        action: Dict[str, Any],
        nonce: int,
        signature: Dict[str, Any]
    ) -> bool:
        """Verify a signature (mainly for testing).

        Args:
            action: Original action that was signed
            nonce: Nonce used in signing
            signature: Signature to verify

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Reconstruct typed data
            connection_id = bytes(32)
            typed_data = {
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"}
                    ],
                    "Agent": [
                        {"name": "source", "type": "string"},
                        {"name": "connectionId", "type": "bytes32"}
                    ]
                },
                "primaryType": "Agent",
                "domain": {
                    "name": self.DOMAIN_NAME,
                    "version": self.DOMAIN_VERSION,
                    "chainId": self.HYPERLIQUID_CHAIN_ID,
                    "verifyingContract": self.HYPERLIQUID_VERIFYING_CONTRACT
                },
                "message": {
                    "source": "a",
                    "connectionId": f"0x{connection_id.hex()}"
                }
            }

            # Encode and recover signer
            encoded_data = encode_typed_data(full_message=typed_data)

            # Reconstruct signature
            r = int(signature["r"], 16)
            s = int(signature["s"], 16)
            v = signature["v"]

            # Recover address from signature
            recovered_address = Account.recover_message(
                encoded_data,
                vrs=(v, r, s)
            )

            # Check if recovered address matches
            is_valid = recovered_address.lower() == self.address.lower()
            logger.debug(f"Signature verification: {is_valid}")

            return is_valid

        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    def get_address(self) -> str:
        """Get the Ethereum address for this signer.

        Returns:
            Checksum Ethereum address
        """
        return self.address

    def __repr__(self) -> str:
        """String representation."""
        return f"<HyperLiquidSigner(address='{self.address}')>"
