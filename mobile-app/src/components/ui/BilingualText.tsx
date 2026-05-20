import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors } from '../../theme/colors';
import { FontSizes, FontWeights, urduStyle } from '../../theme/typography';
import { Space } from '../../theme/spacing';

interface Props {
  english: string;
  urdu: string;
  showUrdu?: boolean;
  englishStyle?: object;
}

export default function BilingualText({ english, urdu, showUrdu = false, englishStyle }: Props) {
  const [expanded, setExpanded] = useState(showUrdu);

  return (
    <View>
      <Text style={[styles.english, englishStyle]}>{english}</Text>
      <TouchableOpacity onPress={() => setExpanded((v) => !v)} style={styles.toggle} hitSlop={8}>
        <Text style={styles.toggleLabel}>{expanded ? '▲ اردو چھپائیں' : '▼ اردو میں پڑھیں'}</Text>
      </TouchableOpacity>
      {expanded && <Text style={[urduStyle.base, styles.urdu]}>{urdu}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  english: {
    fontSize: FontSizes.base,
    color: Colors.textPrimary,
    lineHeight: FontSizes.base * 1.5,
  },
  toggle: {
    marginTop: Space[1],
    paddingVertical: Space[1],
  },
  toggleLabel: {
    fontSize: FontSizes.xs,
    color: Colors.accentSecondary,
    fontWeight: FontWeights.medium,
  },
  urdu: {
    marginTop: Space[2],
    fontSize: FontSizes.base,
  },
});
