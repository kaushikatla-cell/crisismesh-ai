import React, { useEffect, useRef, useState } from "react";
import {
  SafeAreaView,
  View,
  Text,
  TextInput,
  Button,
  FlatList,
  StyleSheet,
} from "react-native";
import TcpSocket from "react-native-tcp-socket";

// Mesh gateway node running chat_server.py
const MESH_SERVER_IP = "10.0.0.1"; // CHANGE THIS
const MESH_SERVER_PORT = 9000;

export default function App() {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const clientRef = useRef(null);

  useEffect(() => {
    const options = {
      port: MESH_SERVER_PORT,
      host: MESH_SERVER_IP,
      reuseAddress: true,
    };

    const client = TcpSocket.createConnection(options, () => {
      console.log("Connected to mesh chat server");
      setConnected(true);
    });

    client.on("data", (data) => {
      const msg = data.toString().trim();
      if (!msg) return;
      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString() + Math.random(), text: msg, from: "node" },
      ]);
    });

    client.on("error", (error) => {
      console.log("TCP error", error);
      setConnected(false);
    });

    client.on("close", () => {
      console.log("Connection closed");
      setConnected(false);
    });

    clientRef.current = client;

    return () => {
      client.destroy();
    };
  }, []);

  const sendMessage = () => {
    if (!clientRef.current || !connected || !input.trim()) return;
    const msg = input.trim();
    clientRef.current.write(msg + "\n");
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), text: msg, from: "me" },
    ]);
    setInput("");
  };

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>CrisisMesh Chat</Text>
      <Text style={styles.status}>
        Status: {connected ? "✅ Connected to mesh" : "❌ Not connected"}
      </Text>

      <FlatList
        style={styles.list}
        data={messages}
        renderItem={({ item }) => (
          <Text style={item.from === "me" ? styles.myMsg : styles.nodeMsg}>
            {item.from === "me" ? "Me: " : "Node: "}
            {item.text}
          </Text>
        )}
        keyExtractor={(item) => item.id}
      />

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Type a message..."
        />
        <Button title="Send" onPress={sendMessage} />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: "#fff" },
  title: { fontSize: 24, fontWeight: "bold", marginBottom: 8 },
  status: { marginBottom: 8 },
  list: { flex: 1, marginVertical: 8 },
  myMsg: { textAlign: "right", marginVertical: 2, color: "#007aff" },
  nodeMsg: { textAlign: "left", marginVertical: 2, color: "#333" },
  inputRow: { flexDirection: "row", alignItems: "center" },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 4,
    padding: 8,
    marginRight: 8,
  },
});
