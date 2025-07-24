import React, { useMemo } from 'react';

interface Entity {
  text: string;
  label: string;
  start: number;
  end: number;
  confidence?: number;
}

interface TerminologyMapping {
  code?: string;
  rxcui?: string;
  display?: string;
  name?: string;
  confidence?: number;
}

interface EntityHighlighterProps {
  text: string;
  entities: Entity[];
  terminologyMappings?: {
    snomed?: Array<{ original_text: string } & TerminologyMapping>;
    loinc?: Array<{ original_text: string } & TerminologyMapping>;
    rxnorm?: Array<{ original_text: string } & TerminologyMapping>;
  };
  maxLength?: number;
}

const ENTITY_COLORS = {
  CONDITION: 'bg-red-100 border-red-300 text-red-800',
  DISEASE: 'bg-red-100 border-red-300 text-red-800',
  SYMPTOM: 'bg-orange-100 border-orange-300 text-orange-800',
  DRUG: 'bg-blue-100 border-blue-300 text-blue-800',
  MEDICATION: 'bg-blue-100 border-blue-300 text-blue-800',
  TEST: 'bg-green-100 border-green-300 text-green-800',
  LAB_TEST: 'bg-green-100 border-green-300 text-green-800',
  OBSERVATION: 'bg-green-100 border-green-300 text-green-800',
  PROCEDURE: 'bg-purple-100 border-purple-300 text-purple-800',
  ANATOMY: 'bg-pink-100 border-pink-300 text-pink-800',
  DOSAGE: 'bg-indigo-100 border-indigo-300 text-indigo-800',
  FREQUENCY: 'bg-yellow-100 border-yellow-300 text-yellow-800',
  DEFAULT: 'bg-gray-100 border-gray-300 text-gray-800'
};

interface HighlightedSegment {
  text: string;
  entity?: Entity;
  isEntity: boolean;
  start: number;
  end: number;
}

export const EntityHighlighter = ({ 
  text, 
  entities, 
  terminologyMappings, 
  maxLength = 2000 
}: EntityHighlighterProps) => {
  const highlightedText = useMemo(() => {
    if (!text || !entities || entities.length === 0) {
      const truncatedText = text?.slice(0, maxLength) || '';
      return [{ 
        text: truncatedText, 
        isEntity: false, 
        start: 0, 
        end: truncatedText.length 
      }];
    }

    // Sort entities by start position
    const sortedEntities = [...entities].sort((a, b) => a.start - b.start);
    
    const segments: HighlightedSegment[] = [];
    let currentPos = 0;

    for (const entity of sortedEntities) {
      // Add text before entity (if any)
      if (currentPos < entity.start) {
        segments.push({
          text: text.slice(currentPos, entity.start),
          isEntity: false,
          start: currentPos,
          end: entity.start
        });
      }

      // Add entity text
      segments.push({
        text: text.slice(entity.start, entity.end),
        entity,
        isEntity: true,
        start: entity.start,
        end: entity.end
      });

      currentPos = entity.end;
    }

    // Add remaining text after last entity
    if (currentPos < text.length) {
      const remainingText = text.slice(currentPos, Math.min(text.length, maxLength));
      segments.push({
        text: remainingText,
        isEntity: false,
        start: currentPos,
        end: currentPos + remainingText.length
      });
    }

    return segments;
  }, [text, entities, maxLength]);

  const getTerminologyMapping = (entityText: string) => {
    if (!terminologyMappings) return null;

    // Check all terminology systems for this entity
    const allMappings = [
      ...(terminologyMappings.snomed || []).map(m => ({ ...m, system: 'SNOMED CT' })),
      ...(terminologyMappings.loinc || []).map(m => ({ ...m, system: 'LOINC' })),
      ...(terminologyMappings.rxnorm || []).map(m => ({ ...m, system: 'RxNorm' }))
    ];

    return allMappings.find(mapping => 
      mapping.original_text?.toLowerCase() === entityText.toLowerCase()
    );
  };

  const EntityTooltip = ({ entity }: { entity: Entity }) => {
    const mapping = getTerminologyMapping(entity.text);
    
    return (
      <div className="absolute z-10 p-3 bg-white border border-gray-300 rounded-lg shadow-lg min-w-64 max-w-80 -mt-2 transform -translate-y-full">
        <div className="space-y-2">
          <div>
            <span className="font-semibold text-gray-900">Entity:</span>
            <span className="ml-2">{entity.text}</span>
          </div>
          <div>
            <span className="font-semibold text-gray-900">Type:</span>
            <span className="ml-2">{entity.label}</span>
          </div>
          {entity.confidence !== undefined && (
            <div>
              <span className="font-semibold text-gray-900">Confidence:</span>
              <span className="ml-2">{(entity.confidence * 100).toFixed(1)}%</span>
            </div>
          )}
          <div>
            <span className="font-semibold text-gray-900">Position:</span>
            <span className="ml-2">{entity.start}-{entity.end}</span>
          </div>
          
          {mapping && (
            <div className="border-t pt-2 mt-2">
              <div className="text-sm text-gray-600 font-semibold mb-1">
                Terminology Mapping:
              </div>
              <div className="space-y-1 text-sm">
                <div>
                  <span className="font-medium">System:</span> {mapping.system}
                </div>
                <div>
                  <span className="font-medium">Code:</span> {mapping.code || mapping.rxcui}
                </div>
                <div>
                  <span className="font-medium">Display:</span> {mapping.display || mapping.name}
                </div>
                {mapping.confidence !== undefined && (
                  <div>
                    <span className="font-medium">Mapping Confidence:</span> {(mapping.confidence * 100).toFixed(1)}%
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
        
        {/* Tooltip arrow */}
        <div className="absolute top-full left-1/2 transform -translate-x-1/2">
          <div className="border-4 border-transparent border-t-white"></div>
          <div className="border-4 border-transparent border-t-gray-300 -mt-1"></div>
        </div>
      </div>
    );
  };

  const [hoveredEntity, setHoveredEntity] = React.useState<Entity | null>(null);

  return (
    <div className="relative">
      <div className="text-sm leading-relaxed whitespace-pre-wrap font-mono">
        {highlightedText.map((segment, index) => {
          if (!segment.isEntity || !segment.entity) {
            return (
              <span key={index} className="text-gray-800">
                {segment.text}
              </span>
            );
          }

          const colorClass = ENTITY_COLORS[segment.entity.label as keyof typeof ENTITY_COLORS] || ENTITY_COLORS.DEFAULT;
          
          return (
            <span key={index} className="relative inline-block">
              <span
                className={`px-1 py-0.5 rounded border cursor-pointer transition-all duration-200 hover:shadow-sm ${colorClass}`}
                onMouseEnter={() => setHoveredEntity(segment.entity!)}
                onMouseLeave={() => setHoveredEntity(null)}
                title={`${segment.entity.label}: ${segment.entity.text}`}
              >
                {segment.text}
              </span>
              
              {hoveredEntity === segment.entity && (
                <EntityTooltip entity={segment.entity} />
              )}
            </span>
          );
        })}
      </div>

      {text.length > maxLength && (
        <div className="mt-2 text-sm text-gray-500 italic">
          Text truncated at {maxLength} characters...
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Entity Types:</h4>
        <div className="flex flex-wrap gap-2">
          {Object.entries(ENTITY_COLORS)
            .filter(([key]) => key !== 'DEFAULT')
            .map(([type, colorClass]) => (
              <span
                key={type}
                className={`px-2 py-1 rounded text-xs ${colorClass} border`}
              >
                {type.replace('_', ' ')}
              </span>
            ))}
        </div>
      </div>
    </div>
  );
};

export default EntityHighlighter;