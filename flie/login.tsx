import { ThemedText } from '@/components/themed-text';
import { apiFetch } from '@/constants/api';
import { saveSession } from '@/lib/session';
import { Image } from 'expo-image';
import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';
import Constants from 'expo-constants';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Animated,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

WebBrowser.maybeCompleteAuthSession();

type GoogleAuthState = {
  idToken: string;
};

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleSubmitting, setIsGoogleSubmitting] = useState(false);
  const [googleState, setGoogleState] = useState<GoogleAuthState | null>(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  const androidClientId =
    process.env.EXPO_PUBLIC_GOOGLE_OAUTH_ANDROID_CLIENT_ID ??
    Constants.expoConfig?.extra?.googleOAuthAndroidClientId ??
    Constants.manifest2?.extra?.expoClient?.extra?.googleOAuthAndroidClientId ??
    'YOUR_ANDROID_CLIENT_ID.apps.googleusercontent.com';

  const iosClientId =
    process.env.EXPO_PUBLIC_GOOGLE_OAUTH_IOS_CLIENT_ID ??
    Constants.expoConfig?.extra?.googleOAuthIosClientId ??
    Constants.manifest2?.extra?.expoClient?.extra?.googleOAuthIosClientId ??
    androidClientId;

  const webClientId =
    process.env.EXPO_PUBLIC_GOOGLE_OAUTH_WEB_CLIENT_ID ??
    Constants.expoConfig?.extra?.googleOAuthWebClientId ??
    Constants.manifest2?.extra?.expoClient?.extra?.googleOAuthWebClientId ??
    androidClientId;

  const clientId = useMemo(
    () =>
      Platform.select({
        ios: iosClientId,
        android: androidClientId,
        web: webClientId,
        default: androidClientId,
      }),
    [androidClientId, iosClientId, webClientId]
  );

  const redirectScheme =
    process.env.EXPO_PUBLIC_GOOGLE_OAUTH_REDIRECT_SCHEME ??
    Constants.expoConfig?.scheme ??
    Constants.manifest2?.extra?.expoClient?.extra?.scheme ??
    'first';

  const useProxy = Platform.select({ web: false, default: true }) ?? false;

  const redirectUri = AuthSession.makeRedirectUri({
    scheme: redirectScheme,
    path: 'oauth2redirect',
    preferLocalhost: Platform.OS === 'web',
    useProxy,
  });

  const discovery = AuthSession.useAutoDiscovery('https://accounts.google.com');

  const [authRequest, , promptAsync] = AuthSession.useAuthRequest(
    clientId
      ? {
          clientId,
          responseType: AuthSession.ResponseType.IdToken,
          scopes: ['openid', 'email', 'profile'],
          redirectUri,
          usePKCE: false,
          extraParams: { nonce: Date.now().toString() },
        }
      : null,
    discovery
  );

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();
    // useRef로 생성된 값은 의존성 배열에 포함할 필요 없음
  }, [fadeAnim, slideAnim]);

  const handleLogin = async () => {
    if (!email || !password) {
      alert('이메일과 비밀번호를 모두 입력해주세요');
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await apiFetch('/auth/login', {
        method: 'POST',
        json: { email, password },
      });

      const body = await res.json().catch(() => null);
      if (!res.ok) {
        const message =
          (body && typeof body === 'object' && 'error' in body && typeof body.error === 'string'
            ? body.error
            : null) ?? '로그인에 실패했습니다';
        alert(message);
        return;
      }

      const token =
        body && typeof body === 'object' && 'token' in body
          ? (body.token as string | undefined)
          : undefined;
      const user =
        body && typeof body === 'object' && 'user' in body
          ? (body.user as Record<string, unknown>)
          : undefined;

      if (!token) {
        alert('로그인 응답이 올바르지 않습니다');
        return;
      }

      await saveSession(token, user ?? {});
      alert('로그인에 성공했습니다');
      router.replace('/');
    } catch (err) {
      console.error(err);
      alert('서버와 통신할 수 없습니다');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleLogin = async () => {
    if (!clientId || clientId === 'YOUR_ANDROID_CLIENT_ID.apps.googleusercontent.com') {
      alert('Google OAuth Client ID를 설정해주세요');
      return;
    }

    if (!authRequest) {
      alert('Google 로그인 구성이 준비되지 않았습니다. 잠시 후 다시 시도해주세요.');
      return;
    }

    try {
      setIsGoogleSubmitting(true);
      setGoogleState(null);

      const result = await promptAsync({ useProxy });

      if (result.type !== 'success') {
        if (result.type !== 'dismiss' && result.type !== 'cancel') {
          const message =
            (result.params && 'error_description' in result.params
              ? String(result.params.error_description)
              : null) ?? 'Google 인증이 취소되었거나 실패했습니다';
          alert(message);
        }
        return;
      }

      const idToken =
        (result.params && 'id_token' in result.params
          ? String(result.params.id_token)
          : null) ?? result.authentication?.idToken;

      if (!idToken) {
        alert('Google ID 토큰을 가져오지 못했습니다');
        return;
      }

      setGoogleState({ idToken });

      const response = await apiFetch('/auth/google/token', {
        method: 'POST',
        json: { id_token: idToken },
      });
      const body = await response.json().catch(() => null);

      if (!response.ok) {
        const message =
          (body && typeof body === 'object' && 'error' in body && typeof body.error === 'string'
            ? body.error
            : null) ?? 'Google 로그인에 실패했습니다';
        alert(message);
        return;
      }

      const token =
        body && typeof body === 'object' && 'token' in body
          ? (body.token as string | undefined)
          : undefined;
      const user =
        body && typeof body === 'object' && 'user' in body
          ? (body.user as Record<string, unknown>)
          : undefined;

      if (!token) {
        alert('로그인 응답이 올바르지 않습니다');
        return;
      }

      await saveSession(token, user ?? {});
      alert('Google 로그인에 성공했습니다');
      router.replace('/');
    } catch (err) {
      console.error(err);
      alert('Google 로그인 중 오류가 발생했습니다');
    } finally {
      setIsGoogleSubmitting(false);
    }
  };

  const handleBack = () => {
    router.back();
  };

  return (
    <LinearGradient
      colors={['#B5E5A8', '#A8D5BA', '#9FD4C7']}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}>
        <Animated.View
          style={[
            styles.content,
            {
              opacity: fadeAnim,
              transform: [{ translateY: slideAnim }],
            },
          ]}>
          {/* 뒤로가기 버튼 */}
          <TouchableOpacity style={styles.backButton} onPress={handleBack}>
            <Text style={styles.backButtonText}>←</Text>
          </TouchableOpacity>

          {/* 로고 */}
          <View style={styles.logoContainer}>
            <LinearGradient
              colors={['#6BC77A', '#52C57A', '#3FC57A']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.logoCircle}>
              <View style={styles.logoInnerCircle}>
                <Image
                  source={require('@/assets/images/Calendar_Icon.png')}
                  style={styles.logoImage}
                  contentFit="contain"
                />
              </View>
            </LinearGradient>
          </View>

          {/* 타이틀 */}
          <ThemedText style={styles.title}>로그인</ThemedText>
          <View style={styles.underline} />

          {/* 입력 폼 */}
          <View style={styles.form}>
            <View style={styles.inputContainer}>
              <Text style={styles.label}>이메일</Text>
              <TextInput
                style={styles.input}
                placeholder="이메일을 입력하세요"
                placeholderTextColor="#999"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <View style={styles.inputContainer}>
              <Text style={styles.label}>비밀번호</Text>
              <TextInput
                style={styles.input}
                placeholder="비밀번호를 입력하세요"
                placeholderTextColor="#999"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                autoCapitalize="none"
              />
            </View>

            {/* 로그인 버튼 */}
            <TouchableOpacity
              style={[
                styles.loginButton,
                isSubmitting ? styles.loginButtonDisabled : null,
              ]}
              onPress={handleLogin}
              disabled={isSubmitting}>
              <Text style={styles.loginButtonText}>
                {isSubmitting ? '처리 중...' : '로그인'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.googleButton,
                isGoogleSubmitting ? styles.loginButtonDisabled : null,
              ]}
              onPress={handleGoogleLogin}
              disabled={isGoogleSubmitting}>
              <Text style={styles.loginButtonText}>
                {isGoogleSubmitting ? 'Google 로그인 중...' : 'Google 계정으로 로그인'}
              </Text>
            </TouchableOpacity>

            {googleState?.idToken ? (
              <Text style={styles.googleStatus}>
                Logged in! ID Token: {googleState.idToken.slice(0, 40)}...
              </Text>
            ) : null}

            {/* 회원가입 링크 */}
            <TouchableOpacity 
              style={styles.signupLink}
              onPress={() => router.push('/signup')}>
              <Text style={styles.signupLinkText}>계정이 없으신가요? 회원가입</Text>
            </TouchableOpacity>
          </View>
        </Animated.View>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 30,
    paddingTop: 60,
    paddingBottom: 40,
    justifyContent: 'center',
  },
  backButton: {
    position: 'absolute',
    top: 60,
    left: 30,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  backButtonText: {
    fontSize: 24,
    color: '#2D8650',
    fontWeight: 'bold',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  logoCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#3FC57A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  logoInnerCircle: {
    width: 110,
    height: 110,
    borderRadius: 55,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoImage: {
    width: 90,
    height: 90,
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: '#2D8650',
    textAlign: 'center',
    marginBottom: 8,
  },
  underline: {
    width: 80,
    height: 4,
    backgroundColor: '#52C57A',
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 40,
  },
  form: {
    width: '100%',
  },
  inputContainer: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2D8650',
    marginBottom: 8,
  },
  input: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#333',
    borderWidth: 1,
    borderColor: 'rgba(82, 197, 122, 0.3)',
  },
  loginButton: {
    backgroundColor: '#52C57A',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 10,
    shadowColor: '#52C57A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  googleButton: {
    backgroundColor: '#EA4335',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 12,
    shadowColor: '#EA4335',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 5,
  },
  loginButtonDisabled: {
    opacity: 0.7,
  },
  loginButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
  },
  googleStatus: {
    marginTop: 16,
    textAlign: 'center',
    color: '#2D8650',
    fontSize: 12,
  },
  signupLink: {
    marginTop: 20,
    alignItems: 'center',
  },
  signupLinkText: {
    color: '#2D8650',
    fontSize: 14,
    fontWeight: '500',
  },
});
