import React, { useState } from 'react';
import { StyleSheet, View, FlatList, TouchableOpacity, Modal, Image, ScrollView } from 'react-native';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useRouter } from 'expo-router';

const regions = [
  { id: '1', name: '강남구', icon: 'location' as const },
  { id: '2', name: '경상북도', icon: 'location' as const },
  { id: '3', name: '경상남도', icon: 'location' as const },
  { id: '4', name: '전라남도', icon: 'location' as const },
  { id: '5', name: '충청북도', icon: 'location' as const },
  { id: '6', name: '충청남도', icon: 'location' as const },
];

// 지역별 위험도 정보
const regionRiskInfo = {
  '강남구': {
    imageUrl: require('../image.png'),
    riskLevel: '중',
    description: '현재 강남구 지역은 중간 수준의 재난 위험이 감지되고 있습니다.',
    details: [
      '• 강수량이 평년 대비 증가한 상태입니다',
      '• 산사태 위험 가능성이 보통입니다',
      '• 주기적인 날씨 정보 확인을 권장합니다',
    ],
  },
  '경상북도': {
    imageUrl: require('../image.png'),
    riskLevel: '낮음',
    description: '경상북도 지역은 비교적 안전한 상태입니다.',
    details: [
      '• 기상 상황이 안정적인 상태입니다',
      '• 특별한 주의사항 없음',
    ],
  },
  '경상남도': {
    imageUrl: require('../image.png'),
    riskLevel: '중',
    description: '경상남도는 해안가 특성상 기상 변화에 주의가 필요합니다.',
    details: [
      '• 해풍으로 인한 날씨 변화 가능성',
      '• 바다 근처 지역의 주의 필요',
    ],
  },
  '전라남도': {
    imageUrl: require('../image.png'),
    riskLevel: '낮음',
    description: '전라남도는 현재 안정적인 기상 상태입니다.',
    details: [
      '• 특별한 재난 위험 없음',
    ],
  },
  '충청북도': {
    imageUrl: require('../image.png'),
    riskLevel: '낮음',
    description: '충청북도 지역은 안전한 상태입니다.',
    details: [
      '• 기상 상황 안정',
    ],
  },
  '충청남도': {
    imageUrl: require('../image.png'),
    riskLevel: '중',
    description: '충청남도는 해안 지역의 영향으로 주의가 필요합니다.',
    details: [
      '• 해안 지역의 기상 변화 주의',
      '• 주기적인 정보 확인 필요',
    ],
  },
};

export default function ListScreen() {
  const router = useRouter();
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);

  const handleRegionPress = (region: string) => {
    setSelectedRegion(region);
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
    setSelectedRegion(null);
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case '높음':
        return '#FF4444';
      case '중':
        return '#FFA500';
      case '낮음':
        return '#4CAF50';
      default:
        return '#666';
    }
  };

  const renderRegionItem = ({ item }: { item: typeof regions[0] }) => (
    <TouchableOpacity 
      style={styles.regionItem} 
      onPress={() => handleRegionPress(item.name)}
    >
      <View style={styles.regionContent}>
        <IconSymbol name={item.icon} size={24} color="#0047AB" />
        <ThemedText style={styles.regionName}>{item.name}</ThemedText>
      </View>
      <IconSymbol name="chevron.right" size={20} color="#666" />
    </TouchableOpacity>
  );

  const regionInfo = selectedRegion ? regionRiskInfo[selectedRegion as keyof typeof regionRiskInfo] : null;

  return (
    <View style={styles.container}>
      <ThemedText type="title" style={styles.title}>
        지역 선택
      </ThemedText>
      <ThemedText style={styles.subtitle}>
        관심 지역을 선택해주세요
      </ThemedText>
      
      <FlatList
        data={regions}
        renderItem={renderRegionItem}
        keyExtractor={(item) => item.id}
        style={styles.list}
        showsVerticalScrollIndicator={false}
      />

      <Modal
        visible={modalVisible}
        transparent={true}
        animationType="fade"
        onRequestClose={closeModal}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <TouchableOpacity 
              style={styles.closeButton} 
              onPress={closeModal}
            >
              <IconSymbol name="xmark" size={24} color="#666" />
            </TouchableOpacity>

            {regionInfo && (
              <ScrollView showsVerticalScrollIndicator={false}>
                <View style={styles.modalHeader}>
                  <ThemedText type="title" style={styles.modalTitle}>
                    {selectedRegion}
                  </ThemedText>
                  <View 
                    style={[
                      styles.riskBadge,
                      { backgroundColor: getRiskColor(regionInfo.riskLevel) }
                    ]}
                  >
                    <ThemedText style={styles.riskLevel}>
                      위험도: {regionInfo.riskLevel}
                    </ThemedText>
                  </View>
                </View>

                <Image 
                  source={regionInfo.imageUrl} 
                  style={styles.modalImage}
                  resizeMode="cover"
                />

                <View style={styles.modalBody}>
                  <ThemedText style={styles.modalDescription}>
                    {regionInfo.description}
                  </ThemedText>

                  <View style={styles.detailsContainer}>
                    {regionInfo.details.map((detail, index) => (
                      <ThemedText key={index} style={styles.detailText}>
                        {detail}
                      </ThemedText>
                    ))}
                  </View>
                </View>
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#87CEEB',
    paddingHorizontal: 20,
    paddingTop: 60,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#0047AB',
    marginBottom: 10,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 30,
  },
  list: {
    flex: 1,
  },
  regionItem: {
    backgroundColor: '#fff',
    paddingVertical: 16,
    paddingHorizontal: 20,
    marginBottom: 12,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  regionContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  regionName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 20,
    width: '90%',
    maxHeight: '80%',
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  closeButton: {
    position: 'absolute',
    top: 15,
    right: 15,
    zIndex: 1,
    padding: 5,
  },
  modalHeader: {
    marginBottom: 20,
    marginTop: 10,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#0047AB',
    marginBottom: 10,
  },
  riskBadge: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    alignSelf: 'flex-start',
  },
  riskLevel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  modalImage: {
    width: '100%',
    height: 200,
    borderRadius: 12,
    marginBottom: 20,
  },
  modalBody: {
    marginBottom: 20,
  },
  modalDescription: {
    fontSize: 16,
    color: '#666',
    lineHeight: 24,
    marginBottom: 20,
  },
  detailsContainer: {
    backgroundColor: '#f8f9fa',
    padding: 16,
    borderRadius: 12,
  },
  detailText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 22,
    marginBottom: 8,
  },
});
