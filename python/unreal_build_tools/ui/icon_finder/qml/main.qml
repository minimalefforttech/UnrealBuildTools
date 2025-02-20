import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

ApplicationWindow {
    visible: true
    width: 1200
    height: 800
    title: "Icon Browser"
    
    Material.theme: Material.Dark
    Material.accent: Material.Blue
    
    function getIconPath(relativePath) {
        let path;
        if (Qt.platform.os === "osx") {
            // Handle macOS .app bundles
            path = [basePath, "UE_" + versionCombo.currentText, "Contents", subPath, relativePath]
                .join('/')
                .replace(/\\/g, '/');
        } else {
            path = [basePath, "UE_" + versionCombo.currentText, subPath, relativePath]
                .join('/')
                .replace(/\\/g, '/');
        }
        
        // Clean up the path
        path = path.replace(/\/+/g, '/');
        
        // Add proper file:// prefix
        if (Qt.platform.os === "windows") {
            return "file:///" + path;
        } else {
            return "file://" + path;
        }
    }
    
    // Add toast popup component
    Popup {
        id: toast
        x: (parent.width - width) / 2
        y: parent.height - height - 40
        width: toastText.width + 40
        height: toastText.height + 20
        modal: false
        
        background: Rectangle {
            color: Material.backgroundColor
            radius: 6
            layer.enabled: true
            
        }
        
        Text {
            id: toastText
            anchors.centerIn: parent
            color: Material.foreground
            text: ""
        }
        
        Timer {
            id: toastTimer
            interval: 2000
            onTriggered: toast.close()
        }
        
        function show(message) {
            toastText.text = message
            toast.open()
            toastTimer.restart()
        }
    }
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 30
        
        Rectangle {
            Layout.fillWidth: true
            height: 48
            color: Material.backgroundColor
            
            // Add subtle bottom border
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Material.dropShadowColor
                opacity: 0.2
            }
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 12
                
                ComboBox {
                    id: versionCombo
                    model: versions
                    currentIndex: count - 1
                    
                    ToolTip.visible: hovered
                    ToolTip.text: "Select Unreal Engine version"
                    ToolTip.delay: 1000
                }
                
                TextField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholderText: "Search icons..."
                    onTextChanged: iconModel.setFilterText(text)
                    Material.containerStyle: Material.Filled
                    Material.accent: Material.Blue
                    
                    ToolTip.visible: hovered
                    ToolTip.text: "Filter icons by name"
                    ToolTip.delay: 1000
                }
                
                Slider {
                    id: sizeSlider
                    from: 16
                    to: 128
                    value: settingsService ? settingsService.loadIconSize(32) : 32  // Load saved value or default
                    Layout.preferredWidth: 100
                    
                    ToolTip.visible: hovered
                    ToolTip.text: "Adjust icon size"
                    ToolTip.delay: 1000
                    
                    // Add property to store the center item
                    property int lastCenterIndex: -1
                    
                    onPressedChanged: {
                        if (pressed) {
                            // Store center item index when starting to drag
                            let centerY = iconGrid.contentY + iconGrid.height / 2
                            lastCenterIndex = iconGrid.indexAt(iconGrid.contentX, centerY)
                        }
                    }
                    
                    onValueChanged: {
                        settingsService.saveIconSize(value)  // Save on change
                        if (pressed && lastCenterIndex >= 0) {
                            // Recalculate position to keep the same item centered
                            iconGrid.positionViewAtIndex(lastCenterIndex, GridView.Center)
                        }
                    }
                }
            }
        }
        
        GridView {
            id: iconGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            
            model: iconModel
            cellWidth: sizeSlider.value + 10
            cellHeight: sizeSlider.value + 10
            
            delegate: Item {
                width: iconGrid.cellWidth
                height: iconGrid.cellHeight
                
                Image {
                    id: iconImage
                    anchors.centerIn: parent
                    width: sizeSlider.value
                    height: sizeSlider.value
                    source: getIconPath(relativePath)
                    sourceSize: Qt.size(sizeSlider.value, sizeSlider.value)
                    fillMode: Image.PreserveAspectFit
                    
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            let path = getIconPath(relativePath)
                            console.log("Icon path: " + path)
                            clipboardService.copy(path)
                            toast.show("Copied to clipboard: " + relativePath)
                        }
                        
                        ToolTip {
                            visible: parent.containsMouse
                            text: relativePath
                            delay: 1000
                            
                            Material.background: Material.toolTipColor
                            Material.foreground: Material.toolTipText
                        }
                    }
                }
            }
            
            ScrollBar.vertical: ScrollBar {}
        }
    }
}
