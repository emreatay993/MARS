# Turkish Documentation Policy - Technical Terms

**Date:** November 22, 2025  
**Policy:** Keep technical terms in English in Turkish documentation  
**Scope:** All Turkish documentation including UAT tests

---

## Policy Statement

**When writing Turkish documentation for MARS, core technical terms should be kept in English and NOT translated to Turkish.**

---

## Technical Terms to Keep in English

### Core Technical Terms:

| English Term | Keep As | ~~Do NOT Use~~ | Context |
|--------------|---------|----------------|---------|
| Relative Mode | **Relative Mode** | ~~Göreceli Mod~~ | Animation deformation display |
| Absolute Mode | **Absolute Mode** | ~~Mutlak Mod~~ | Animation deformation display |
| Deformation | **Deformation** | ~~Deformasyon~~ | When referring to technical concept |
| Undeformed | **Undeformed** | ~~Deformasyonsuz~~ | Original geometry state |
| Frame | **Frame** | ~~Çerçeve/Kare~~ | Animation frames |
| Checkbox | **Checkbox** | ~~Onay kutusu~~ | UI element |
| Von Mises | **Von Mises** | ~~Von Mises~~ | Stress calculation method |
| Principal Stress | **Principal Stress** | ~~Ana Gerilme~~ | Stress component |
| Modal | **Modal** | ~~Modal~~ | Modal analysis |
| Node | **Node** | ~~Düğüm~~ | FEA node |
| Mesh | **Mesh** | ~~Ağ~~ | FEA mesh |

### UI Element Names:
Always keep UI element names in English as they appear in the application:
- "Show Absolute Deformations" → **"Show Absolute Deformations"**
- "Visualization Controls" → **"Visualization Controls"**
- "Play" / "Pause" / "Stop" → **"Play" / "Pause" / "Stop"**
- "Update" / "Save" → **"Update" / "Save"**

### File Extensions and Formats:
- `.mcf`, `.csv`, `.txt`, `.dat` → Keep as-is
- `MP4`, `GIF`, `APDL` → Keep as-is

---

## Rationale

### Why Keep Terms in English?

1. **UI Consistency** ✅
   - UI elements are shown in English
   - Documentation should match what users see
   - Reduces confusion when following instructions

2. **Technical Precision** ✅
   - English terms are unambiguous in engineering context
   - Turkish translations may have multiple meanings
   - Industry standard practice

3. **International Standards** ✅
   - Engineering documents commonly use English technical terms
   - Easier for international collaboration
   - Consistent with academic and professional literature

4. **Search and Reference** ✅
   - Users can search for English terms in code and docs
   - Stack Overflow and technical forums use English terms
   - Documentation searchability improved

5. **Educational Value** ✅
   - Users learn standard English technical terminology
   - Prepares users for international technical communication
   - Aligns with engineering education standards

---

## What SHOULD Be Translated

### Instructions and Explanations:

| Turkish Translation | English | Usage |
|---------------------|---------|-------|
| "tıklayın" | "click" | Action instructions |
| "doğrulayın" | "verify" | Verification steps |
| "gözlemleyin" | "observe" | Observation steps |
| "başlangıç" | "start/beginning" | Descriptive text |
| "görünür" | "visible" | State descriptions |
| "etkinleştirin" | "enable" | Action instructions |
| "seçin" | "select" | Selection actions |

### Descriptive Text:
- Test descriptions
- Test step instructions
- Expected result explanations
- Notes and tips

---

## Examples

### ✅ CORRECT - Mixed Turkish/English:

```
TEST ADIMLARI:

1. Solver tamamlandıktan sonra Display sekmesine geçin
2. Visualization Controls grubunda "Show Absolute Deformations" checkbox'ını bulun
3. Checkbox'ın görünür olduğunu ve varsayılan olarak işaretlenmediğini (Relative Mode) doğrulayın
4. Relative Mode'da animasyonu başlatmak için Play'e tıklayın
5. İlk animasyon frame'inin undeformed mesh pozisyonunda göründüğünü gözlemleyin
```

**Why this is correct:**
- Actions/verbs in Turkish (tıklayın, doğrulayın, gözlemleyin)
- Technical terms in English (Relative Mode, undeformed, mesh)
- UI element names in English ("Show Absolute Deformations")
- Natural and clear to Turkish engineering audience

### ❌ INCORRECT - All Turkish:

```
TEST ADIMLARI:

1. Çözücü tamamlandıktan sonra Görüntü sekmesine geçin
2. Görselleştirme Kontrolleri grubunda "Mutlak Deformasyonları Göster" onay kutusunu bulun
3. Onay kutusunun görünür olduğunu ve varsayılan olarak işaretlenmediğini (Göreceli Mod) doğrulayın
4. Göreceli Mod'da animasyonu başlatmak için Oynat'a tıklayın
5. İlk animasyon çerçevesinin deformasyonsuz ağ pozisyonunda göründüğünü gözlemleyin
```

**Why this is wrong:**
- Translated UI elements don't match actual application
- User will be confused looking for "Mutlak Deformasyonları Göster"
- "Çözücü" for "Solver" is technically correct but not standard in engineering
- Harder to reference in code and documentation

### ❌ INCORRECT - All English:

```
TEST STEPS:

1. After Solver completes, switch to Display tab
2. Locate "Show Absolute Deformations" checkbox in Visualization Controls group
3. Verify checkbox is visible and unchecked by default (Relative Mode)
4. Click Play to start animation in Relative Mode
5. Observe first animation frame appears at undeformed mesh position
```

**Why this is wrong:**
- Defeats the purpose of Turkish documentation
- Turkish users may not be fluent in English
- Instructions should be accessible to Turkish-speaking team

---

## Implementation Guidelines

### For Documentation Writers:

1. **Identify Technical Terms:**
   - Ask: "Is this a technical engineering term?"
   - Ask: "Does this appear in the UI?"
   - If YES → Keep in English

2. **Translate Actions and Descriptions:**
   - Actions: "click" → "tıklayın"
   - States: "visible" → "görünür"
   - Verbs: "verify" → "doğrulayın"

3. **Quote UI Elements Exactly:**
   - Use quotation marks: "Show Absolute Deformations"
   - Keep exact capitalization
   - Don't translate content in quotes

4. **Use Natural Turkish Grammar:**
   - Turkish case endings on English technical terms are OK
   - Example: "Relative Mode'da" (locative case)
   - Example: "checkbox'ını" (accusative case)

### For Translators:

✅ **Translate:**
- Action verbs (click, verify, select)
- Descriptive adjectives (visible, enabled, correct)
- Explanatory text (descriptions, notes)
- Test instructions
- Expected results descriptions

❌ **Do NOT Translate:**
- Technical engineering terms
- UI element labels
- Button names
- Menu items
- File extensions
- Software names
- Method names (Neuber, Glinka, IBG)

---

## Existing Turkish Documentation

### Files Following This Policy:
- ✅ `MARS_UAT_Tests_Turkish.txt` - Now updated with policy
- Review other Turkish docs if any exist

### Consistency Check:
If you have other Turkish documentation, verify:
- [ ] Technical terms in English
- [ ] UI elements not translated
- [ ] Instructions in Turkish
- [ ] Natural Turkish grammar with English technical terms

---

## Benefits of This Approach

### For Users:
✅ Match documentation to actual UI easily  
✅ Learn standard English technical terminology  
✅ Clear instructions in native language  
✅ Reduced confusion from mistranslations

### For Maintainers:
✅ Easier to keep docs synchronized  
✅ Technical terms don't need retranslation  
✅ Less risk of translation errors  
✅ Faster documentation updates

### For International Teams:
✅ Turkish and English teams can collaborate  
✅ Technical discussions use common terms  
✅ Code and documentation alignment  
✅ Standard engineering practice

---

## Cross-Reference with Similar Projects

This policy aligns with:
- ANSYS documentation in various languages
- Abaqus international manuals
- AutoCAD localized versions
- MATLAB documentation standards

All keep technical terms in English while translating instructional content.

---

## Review Checklist

When reviewing Turkish documentation:

- [ ] Technical engineering terms in English
- [ ] UI element names match application exactly
- [ ] Action verbs translated to Turkish
- [ ] Instructions clear and natural in Turkish
- [ ] No awkward literal translations
- [ ] Turkish grammar correct (including English term declension)
- [ ] Consistent with existing Turkish documentation style

---

## Application to This Feature

### Feature Name:
**English:** "Animation Deformation Display Modes - Relative vs Absolute"  
**Turkish:** "Animation Deformation Görüntüleme Modları - Relative ve Absolute"

**Analysis:**
- "Animation" → Kept (technical term, UI uses English)
- "Deformation" → Kept (technical term)
- "Görüntüleme Modları" → Translated ("Display Modes")
- "Relative" → Kept (mode name)
- "Absolute" → Kept (mode name)

### Test Content:
- "Relative Mode" appears 6+ times → All kept in English ✅
- "Absolute Mode" appears 6+ times → All kept in English ✅
- "Undeformed" appears 2 times → All kept in English ✅
- "Deformed" appears 2 times → All kept in English ✅

---

## Future Application

Apply this policy to:
- Future feature documentation in Turkish
- Updates to existing Turkish documentation
- User manuals if created in Turkish
- Training materials in Turkish
- Help documentation in Turkish

---

## Contact for Questions

If uncertain whether a term should be translated:
1. Check if it appears in the UI → Keep English
2. Check if it's a standard engineering term → Keep English
3. Check existing Turkish docs for precedent
4. When in doubt → Keep English

---

## Conclusion

This policy provides clear guidelines for creating Turkish technical documentation that:
- ✅ Maintains technical precision
- ✅ Aligns with UI implementation
- ✅ Follows engineering documentation best practices
- ✅ Serves Turkish-speaking users effectively

**All Turkish UAT documentation now follows this policy.**

