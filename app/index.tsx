import React from 'react';
import { StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { ThemedText } from '@/components/themed-text';
//import { ThemedView } from '@/components/themed-view';
import { View } from 'react-native';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useRouter } from 'expo-router';

export default function WelcomeScreen() {
  const router = useRouter();

  const handleStart = () => {
    router.push('/List');
  };

  const handleLogin = () => {
    Alert.alert('로그인', '로그인 기능은 추후 구현 예정입니다.', [
      { text: '확인', onPress: () => {} }
    ]);
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        {/* 앱 로고/아이콘 */}
        <View style={styles.logoContainer}>
          <IconSymbol name="calendar" size={80} color="#87CEEB" />
        </View>

        {/* 앱 이름 */}
        <ThemedText type="title" style={styles.appTitle}>
          Disaster System
        </ThemedText>
        
        <ThemedText style={styles.subtitle}>
          사전에 재난을 방지하세요
        </ThemedText>

        {/* 버튼들 */}
        <View style={styles.buttonContainer}>
          <TouchableOpacity style={styles.startButton} onPress={handleStart}>
            <ThemedText style={styles.startButtonText}>시작하기</ThemedText>
            <IconSymbol name="arrow.right" size={20} color="#fff" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.loginButton} onPress={handleLogin}>
            <ThemedText style={styles.loginButtonText}>로그인하기</ThemedText>
            <IconSymbol name="person" size={20} color="#87CEEB" />
          </TouchableOpacity>
        </View>

        {/* 추가 정보 */}
        <View style={styles.infoContainer}>
          <ThemedText style={styles.infoText}>
            계정 없이도 사용할 수 있습니다
          </ThemedText>
        </View>
      </View>

      {/* 하단 정보 */}
      <View style={styles.footer}>
        <ThemedText style={styles.footerText}>
          System v1.0
        </ThemedText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#87CEEB',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  logoContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  appTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#0047AB',
    marginBottom: 10,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 50,
    lineHeight: 24,
  },
  buttonContainer: {
    width: '100%',
    gap: 15,
  },
  startButton: {
    backgroundColor: '#0047AB',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  startButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  loginButton: {
    backgroundColor: '#fff',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    borderWidth: 2,
    borderColor: '#0047AB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  loginButtonText: {
    color: '#0047AB',
    fontSize: 18,
    fontWeight: 'bold',
  },
  infoContainer: {
    marginTop: 40,
    paddingHorizontal: 20,
  },
  infoText: {
    fontSize: 14,
    color: '#888',
    textAlign: 'center',
    lineHeight: 20,
  },
  footer: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#999',
  },
});